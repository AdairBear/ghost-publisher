#!/usr/bin/env python3
"""Attach a Trident share card to a Ghost post as its OG / social image.

Reads a post by slug, picks the card tier from the post's internal tag
(#field-note / #short-form-note / #signal / #digest), renders the card, uploads
it to Ghost, and sets `feature_image`, `og_image` and `twitter_image`.

Credentials are NOT re-declared here. They come from the existing publishing
pipeline's loader (`ghost_publisher.config.load_credentials`), which reads
GHOST_ADMIN_API_KEY / GHOST_API_URL from the project `.env`. The JWT is minted
by the pipeline's `ghost_client.make_jwt`, so there is one auth implementation
in this repo, not two. No PyJWT dependency.

Safety: by default this refuses to touch a post that is not a draft. Pass
`--allow-published` to override, deliberately and explicitly.

Usage:
    ../.venv/bin/python ghost_og_card.py --slug my-post --dry-run
    ../.venv/bin/python ghost_og_card.py --slug my-post
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import make_card  # noqa: E402  (sibling module, same directory)
from ghost_publisher.config import ConfigError, load_credentials  # noqa: E402
from ghost_publisher.ghost_client import make_jwt  # noqa: E402

logger = logging.getLogger("ghost_og_card")

ADMIN_API_PATH = "/ghost/api/admin"
ACCEPT_VERSION = "v5.0"
TIMEOUT = 60

# Ghost internal tag -> card tier.
TAG_TIERS = {
    "#field-note": "field",
    "#short-form-note": "shortform",
    "#signal": "signal",
    "#digest": "digest",
}
FALLBACK_TIER = "field"


class CardError(Exception):
    """Raised when the card cannot be built or attached."""


def _auth_headers(creds: Any, *, json_body: bool = True) -> dict[str, str]:
    """Build Admin API auth headers.

    Args:
        creds: The loaded `Credentials`.
        json_body: Whether to declare a JSON content type. Must be False for
            multipart uploads so `requests` can set its own boundary.

    Returns:
        The request headers.
    """
    token = make_jwt(creds.key_id, creds.key_secret)
    headers = {
        "Authorization": f"Ghost {token}",
        "Accept-Version": ACCEPT_VERSION,
        "User-Agent": "ghost-og-card/0.1",
    }
    if json_body:
        headers["Content-Type"] = "application/json"
    return headers


def _describe_error(response: requests.Response) -> str:
    """Summarise a Ghost error response in one line.

    Args:
        response: The failed response.

    Returns:
        A short human-readable description.
    """
    try:
        errors = response.json().get("errors") or []
        detail = "; ".join(e.get("message", "?") for e in errors) or response.text[:300]
    except ValueError:
        detail = response.text[:300]
    return f"HTTP {response.status_code}: {detail}"


def fetch_post(base_url: str, creds: Any, slug: str) -> dict[str, Any]:
    """Fetch a post by slug, including its tags.

    Args:
        base_url: Admin API root, no trailing slash.
        creds: The loaded `Credentials`.
        slug: The post slug.

    Returns:
        The post dict.

    Raises:
        CardError: The post does not exist or the request failed.
    """
    url = f"{base_url}/posts/slug/{slug}/"
    response = requests.get(
        url,
        headers=_auth_headers(creds),
        params={"formats": "html", "include": "tags"},
        timeout=TIMEOUT,
    )
    if response.status_code == 404:
        raise CardError(f"no post with slug {slug!r}")
    if not response.ok:
        raise CardError(f"post lookup failed — {_describe_error(response)}")
    posts = response.json().get("posts") or []
    if not posts:
        raise CardError(f"no post with slug {slug!r}")
    return posts[0]


def tier_from_post(post: dict[str, Any]) -> str:
    """Pick the card tier from the post's internal tags.

    Args:
        post: The fetched post dict.

    Returns:
        A tier key valid for `make_card.TIERS`.
    """
    for tag in post.get("tags") or []:
        name = (tag.get("name") or "").strip().lower()
        if name in TAG_TIERS:
            return TAG_TIERS[name]
    logger.warning(
        "no tier tag on post (looked for %s) — defaulting to %r",
        ", ".join(TAG_TIERS),
        FALLBACK_TIER,
    )
    return FALLBACK_TIER


def upload_image(base_url: str, creds: Any, png_path: Path) -> str:
    """Upload a PNG to Ghost's image store.

    Args:
        base_url: Admin API root, no trailing slash.
        creds: The loaded `Credentials`.
        png_path: Local path to the rendered card.

    Returns:
        The public URL Ghost assigned to the image.

    Raises:
        CardError: The upload failed or the response was unexpected.
    """
    url = f"{base_url}/images/upload/"
    with png_path.open("rb") as handle:
        response = requests.post(
            url,
            headers=_auth_headers(creds, json_body=False),
            files={"file": (png_path.name, handle, "image/png")},
            data={"purpose": "image", "ref": png_path.name},
            timeout=TIMEOUT,
        )
    if not response.ok:
        raise CardError(f"image upload failed — {_describe_error(response)}")
    try:
        return response.json()["images"][0]["url"]
    except (ValueError, KeyError, IndexError) as exc:
        raise CardError(f"Ghost returned an unexpected upload body: {response.text[:300]}") from exc


def attach_image(
    base_url: str,
    creds: Any,
    post: dict[str, Any],
    image_url: str,
    *,
    set_header: bool = False,
) -> dict[str, Any]:
    """Set the social-share images on a post.

    Sets `og_image` and `twitter_image` only. The post's `feature_image`
    (header art) is never touched unless `set_header` is True.

    Args:
        set_header: Also overwrite `feature_image` with the card.
        base_url: Admin API root, no trailing slash.
        creds: The loaded `Credentials`.
        post: The previously fetched post, for its id and `updated_at`.
        image_url: The uploaded card URL.

    Returns:
        The updated post dict.

    Raises:
        CardError: The update failed. A 409 means the post changed since it was
            fetched — re-run to pick up the newer `updated_at`.
    """
    url = f"{base_url}/posts/{post['id']}/"
    fields: dict[str, Any] = {
        "updated_at": post["updated_at"],
        "og_image": image_url,
        "twitter_image": image_url,
    }
    # `feature_image` is the in-post header image, not the social card. It is
    # left alone unless explicitly requested, so attaching a card to a live post
    # can never silently replace its header art.
    if set_header:
        fields["feature_image"] = image_url
    body = {"posts": [fields]}
    response = requests.put(url, headers=_auth_headers(creds), json=body, timeout=TIMEOUT)
    if response.status_code == 409:
        raise CardError("post was modified since it was read (409) — re-run to retry")
    if not response.ok:
        raise CardError(f"post update failed — {_describe_error(response)}")
    return response.json()["posts"][0]


def main() -> int:
    """CLI entry point.

    Returns:
        Process exit code.
    """
    ap = argparse.ArgumentParser(description="Attach a Trident OG card to a Ghost post.")
    ap.add_argument("--slug", required=True, help="Slug of the post to card.")
    ap.add_argument("--tier", default=None, help="Override the tag-derived tier.")
    ap.add_argument("--kick", default=None, help="Override the kicker line.")
    ap.add_argument("--title", default=None, help="Override the card title.")
    ap.add_argument("--sub", default=None, help="Override the sub-headline.")
    ap.add_argument("--num", default="01", help="Issue number shown on the card.")
    ap.add_argument("--pill", default=None, help="Override the pill label.")
    ap.add_argument("--out", default=None, help="Where to write the PNG.")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Render the card locally and stop. Does not call Ghost.",
    )
    ap.add_argument(
        "--allow-published",
        action="store_true",
        help="Permit modifying a post that is not a draft. Off by default.",
    )
    ap.add_argument(
        "--set-header",
        action="store_true",
        help="Also replace the post's header image (feature_image) with the "
        "card. Off by default — only og_image and twitter_image are set.",
    )
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    try:
        creds = load_credentials(PROJECT_ROOT / ".env", required=True)
    except ConfigError as exc:
        logger.error("credentials: %s", exc)
        return 2
    base_url = f"{creds.api_url}{ADMIN_API_PATH}"

    # A dry run with no overrides still needs the post for its title, so fetch
    # unless the caller supplied everything the card needs.
    post: dict[str, Any] = {}
    if not (args.dry_run and args.title):
        try:
            post = fetch_post(base_url, creds, args.slug)
        except CardError as exc:
            logger.error("%s", exc)
            return 1
        logger.info(
            "post %r found: status=%s, updated_at=%s",
            args.slug,
            post.get("status"),
            post.get("updated_at"),
        )

    tier = args.tier or (tier_from_post(post) if post else FALLBACK_TIER)
    if tier not in make_card.TIERS:
        logger.error("unknown tier %r (expected one of %s)", tier, ", ".join(make_card.TIERS))
        return 2

    title = args.title or post.get("title") or args.slug
    sub = args.sub or post.get("custom_excerpt") or ""
    kick = args.kick or make_card.DEFAULT_KICK[tier]
    out_path = Path(args.out or (Path(__file__).parent / f"card-{args.slug}.png"))

    svg = make_card.build_svg(tier, args.num, kick, title, sub, args.pill)
    make_card.render_png(svg, str(out_path))
    logger.info("rendered %s (tier=%s)", out_path, tier)

    if args.dry_run:
        logger.info("dry run — Ghost was not modified")
        return 0

    status = post.get("status")
    if status != "draft" and not args.allow_published:
        logger.error(
            "refusing to modify post %r with status=%s. Card rendered at %s. "
            "Re-run with --allow-published to attach it.",
            args.slug,
            status,
            out_path,
        )
        return 3

    try:
        image_url = upload_image(base_url, creds, out_path)
        logger.info("uploaded card: %s", image_url)
        updated = attach_image(base_url, creds, post, image_url, set_header=args.set_header)
    except CardError as exc:
        logger.error("%s", exc)
        return 1

    logger.info(
        "attached to %r — og_image=%s twitter_image=%s feature_image=%s",
        args.slug,
        updated.get("og_image"),
        updated.get("twitter_image"),
        updated.get("feature_image"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
