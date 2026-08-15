"""Command line entry point.

    python -m ghost_publisher run --dry-run
    python -m ghost_publisher run
    python -m ghost_publisher status

Exit codes:
    0  success, or nothing to do (empty queue is not an error)
    1  unexpected failure
    2  configuration or credential problem
    3  refused for safety (already published, slug taken)
"""

from __future__ import annotations

import argparse
import logging
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from . import __version__
from .config import (
    Config,
    ConfigError,
    Credentials,
    load_config,
    load_credentials,
)

from .ghost_client import (
    GhostApiError,
    GhostClient,
    build_post_payload,
    slugify,
)
from .logging_setup import configure_logging
from .queue import QueueError, QueueItem, list_queue, next_publishable
from .render import RenderError, markdown_to_html
from .scheduling import ScheduleError, next_slot, to_ghost_timestamp
from .state import PublishRecord, State, StateError

# Frontmatter tag -> card tier. Accepts the public tag a piece already carries
# ("field-notes") as well as the internal tier tag ("#field-note").
TIER_BY_TAG = {
    "field-notes": "field",
    "#field-note": "field",
    "short-form-note": "shortform",
    "#short-form-note": "shortform",
    "signal": "signal",
    "#signal": "signal",
    "digest": "digest",
    "#digest": "digest",
}

# Internal tier tag written onto every new post, so tier is machine-readable.
TIER_TAG = {
    "field": "#field-note",
    "shortform": "#short-form-note",
    "signal": "#signal",
    "digest": "#digest",
}

logger = logging.getLogger("ghost_publisher")

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_CONFIG = 2
EXIT_REFUSED = 3

DEFAULT_ROOT = Path(__file__).resolve().parent.parent


def _tier_for(item: QueueItem) -> str:
    """Resolve a piece's card tier from its frontmatter tags.

    Args:
        item: The queue item.

    Returns:
        A tier key, defaulting to `field` when no tier tag is present.
    """
    for tag in item.tags:
        tier = TIER_BY_TAG.get(tag.strip().lower())
        if tier:
            return tier
    return "field"


def _issue_number(filename: str) -> str:
    """Pull the issue number from a numbered queue filename.

    `10-trident-report.md` -> `10`. Falls back to `01` when the filename
    carries no numeric prefix.

    Args:
        filename: The queue file's basename.

    Returns:
        The issue number as a string.
    """
    match = re.match(r"(\d+)", filename)
    return match.group(1) if match else "01"


def _attach_share_card(config: Config, credentials: Credentials, created: dict, item: QueueItem) -> None:
    """Render and attach the branded OG card to a freshly created post.

    Fail-soft by design: the post is already created, recorded in state and
    archived by this point, so a card failure must never abort the run or
    surface as a publishing error. It logs at WARNING and returns.

    The draft-only guard in the CLI is deliberately bypassed here — the
    pipeline created this post moments ago, so writing to it is not the
    "modifying someone's live post" case that guard exists to prevent. Only
    `og_image` / `twitter_image` are set; the header image is left alone.

    Args:
        config: The resolved run config.
        credentials: Ghost credentials already loaded for this run.
        created: The post dict returned by `create_post`.
        item: The queue item the post was built from.
    """
    try:
        sys.path.insert(0, str(config.paths.root / "share_cards"))
        import ghost_og_card
        import make_card

        tier = _tier_for(item)
        num = _issue_number(item.path.name)
        svg = make_card.build_svg(
            tier,
            num,
            make_card.DEFAULT_KICK[tier],
            item.title,
            item.excerpt or "",
        )
        out = config.paths.root / "share_cards" / f"card-{created['slug']}.png"
        make_card.render_png(svg, str(out))

        base_url = f"{credentials.api_url}/ghost/api/admin"
        image_url = ghost_og_card.upload_image(base_url, credentials, out)
        ghost_og_card.attach_image(base_url, credentials, created, image_url)
        logger.info("share card attached (tier=%s, N%s): %s", tier, num, image_url)
    except Exception as exc:  # noqa: BLE001 — cosmetic step, never break publishing
        logger.warning(
            "share card not attached to %s (post itself is fine): %s",
            created.get("slug"),
            exc,
        )


def _resolve_slug(item: QueueItem) -> str:
    """Explicit frontmatter slug if given, otherwise one derived from the title."""
    return slugify(item.slug) if item.slug else slugify(item.title)


def _archive(item: QueueItem, published_dir: Path, slot: datetime) -> Path:
    """Move a published piece out of the queue into `published/`.

    Args:
        item: The item that was just scheduled.
        published_dir: Destination directory.
        slot: The slot it was scheduled for, used as a filename prefix.

    Returns:
        The new path of the file.
    """
    published_dir.mkdir(parents=True, exist_ok=True)
    stem = item.path.name
    destination = published_dir / f"{slot.strftime('%Y-%m-%d')}-{stem}"
    counter = 2
    while destination.exists():
        destination = published_dir / f"{slot.strftime('%Y-%m-%d')}-{counter}-{stem}"
        counter += 1
    shutil.move(str(item.path), str(destination))
    return destination


def command_run(config: Config, *, dry_run: bool, force: bool, web_only: bool = False) -> int:
    """Schedule the top queued piece on Ghost.

    Args:
        config: Resolved configuration.
        dry_run: Render and compute everything, but make no API call and change
            no files. Works without any credentials.
        force: Proceed even if local state or Ghost says this piece exists.
        web_only: Publish without emailing the newsletter, overriding the
            configured default for this run only.

    Returns:
        A process exit code.
    """
    mode = "DRY RUN" if dry_run else "LIVE"
    logger.info("ghost-publisher %s — %s run", __version__, mode)

    state = State.load(config.paths.state_file)
    items = list_queue(config.paths.queue_dir)
    logger.info("queue: %d file(s) in %s", len(items), config.paths.queue_dir)

    item = next_publishable(items)
    if item is None:
        logger.info("nothing ready to publish — queue is empty or all items are on hold")
        return EXIT_OK

    slug = _resolve_slug(item)
    logger.info("selected: %s  (title=%r, slug=%s)", item.path.name, item.title, slug)

    duplicate = state.find_duplicate(source_file=item.path.name, content_hash=item.content_hash)
    if duplicate and not force:
        logger.error(
            "REFUSING: %s was already published on %s as post %s (%s). "
            "Use --force only if you are certain you want a second copy.",
            item.path.name,
            duplicate.created_at,
            duplicate.post_id,
            duplicate.post_url,
        )
        return EXIT_REFUSED
    if duplicate and force:
        logger.warning("--force: proceeding despite existing record %s", duplicate.post_id)

    slot = next_slot(config.cadence, after=state.last_scheduled_at())
    published_at = to_ghost_timestamp(slot)
    logger.info(
        "next %s slot: %s (%s) -> published_at %s",
        config.cadence.every,
        slot.strftime("%A %Y-%m-%d %H:%M"),
        slot.tzname(),
        published_at,
    )

    html = markdown_to_html(item.body)
    payload = build_post_payload(
        title=item.title,
        html=html,
        slug=slug,
        published_at=published_at,
        tags=[*item.tags, TIER_TAG[_tier_for(item)]],
        featured=item.featured,
        excerpt=item.excerpt,
        defaults=config.post,
    )

    # Email routing. Default is to send to the configured newsletter; a piece
    # opts out with `web_only: true` in frontmatter or the --web-only flag.
    # Ghost binds the newsletter at the status transition into scheduled, so
    # this can only be set at creation time — not patched onto a post later.
    send_web_only = web_only or item.web_only
    email_params: dict[str, str] = {}
    if config.post.send_email and not send_web_only:
        if not config.post.newsletter:
            logger.error(
                "post.send_email is true but post.newsletter is unset — set the "
                "newsletter slug in config.yaml, or set send_email: false."
            )
            return EXIT_CONFIG
        email_params = {
            "newsletter": config.post.newsletter,
            "email_segment": config.post.email_segment,
        }
        logger.info(
            "email: will send to newsletter %r (segment %s) on publish",
            config.post.newsletter,
            config.post.email_segment,
        )
    else:
        reason = "web_only" if send_web_only else "post.send_email is false"
        logger.info("email: web-only, no newsletter attached (%s)", reason)

    if dry_run:
        post = payload["posts"][0]
        logger.info("--- DRY RUN: no API call, no files touched ---")
        logger.info("  title:        %s", post["title"])
        logger.info("  slug:         %s", post["slug"])
        logger.info("  status:       %s", post["status"])
        logger.info("  published_at: %s", post.get("published_at", "(n/a)"))
        logger.info("  featured:     %s", post["featured"])
        logger.info("  tags:         %s", [t["name"] for t in post.get("tags", [])] or "(none)")
        logger.info("  excerpt:      %s", post.get("custom_excerpt", "(none)"))
        logger.info("  html bytes:   %d", len(post["html"]))
        logger.info(
            "  email:        %s",
            f"newsletter={email_params['newsletter']} segment={email_params['email_segment']}"
            if email_params
            else "(web-only, no email)",
        )
        logger.info("  html preview: %s", post["html"][:200].replace("\n", " "))
        logger.info("  would archive %s -> %s/", item.path.name, config.paths.published_dir.name)
        logger.info("--- end dry run ---")
        return EXIT_OK

    # required=True raises rather than returning None; the explicit check is
    # here because `assert` is stripped under `python -O`.
    credentials = load_credentials(config.paths.root / ".env", required=True)
    if credentials is None:  # pragma: no cover - unreachable via required=True
        raise ConfigError("credentials could not be loaded")
    client = GhostClient(credentials, config.api)
    logger.info("Ghost target: %s", client.base_url)

    existing = client.find_post_by_slug(slug)
    if existing and not force:
        logger.error(
            "REFUSING: a post with slug %r already exists on Ghost "
            "(id=%s, status=%s). Rename the piece, set a different `slug:` in "
            "frontmatter, or re-run with --force.",
            slug,
            existing.get("id"),
            existing.get("status"),
        )
        return EXIT_REFUSED
    if existing and force:
        logger.warning("--force: slug %r already exists on Ghost; Ghost will de-duplicate it", slug)

    created = client.create_post(payload, params=email_params)
    logger.info(
        "created post id=%s status=%s url=%s",
        created.get("id"),
        created.get("status"),
        created.get("url"),
    )

    # State is written BEFORE the file move: if the move fails, the record still
    # exists and the next run refuses to republish.
    state.add(
        PublishRecord(
            source_file=item.path.name,
            content_hash=item.content_hash,
            title=item.title,
            post_id=str(created.get("id", "")),
            post_url=str(created.get("url", "")),
            slug=str(created.get("slug", slug)),
            scheduled_at=str(created.get("published_at", published_at)),
            created_at=datetime.now().astimezone().isoformat(timespec="seconds"),
            dry_run=False,
        )
    )

    destination = _archive(item, config.paths.published_dir, slot)
    logger.info("archived %s -> %s", item.path.name, destination.relative_to(config.paths.root))

    _attach_share_card(config, credentials, created, item)
    logger.info(
        "DONE — Ghost will publish %r at %s (%s)",
        item.title,
        slot.strftime("%A %Y-%m-%d %H:%M"),
        slot.tzname(),
    )
    return EXIT_OK


def command_status(config: Config) -> int:
    """Print the queue, the next slot, and what has already gone out.

    Args:
        config: Resolved configuration.

    Returns:
        A process exit code.
    """
    state = State.load(config.paths.state_file)
    items = list_queue(config.paths.queue_dir)

    print(f"ghost-publisher {__version__}")
    print(f"project root : {config.paths.root}")
    print(
        f"cadence      : {config.cadence.every} "
        f"{config.cadence.weekday} {config.cadence.time} "
        f"({config.cadence.timezone}), min lead {config.cadence.min_lead_minutes}m"
    )

    credentials = load_credentials(config.paths.root / ".env", required=False)
    if credentials:
        print(f"credentials  : OK (key id {credentials.key_id[:6]}…, {credentials.api_url})")
    else:
        print("credentials  : NOT configured — dry-run only (see env.example)")

    slot = next_slot(config.cadence, after=state.last_scheduled_at())
    print(f"next slot    : {slot.strftime('%A %Y-%m-%d %H:%M %Z')}")

    print(f"\nqueue ({config.paths.queue_dir.name}/):")
    if not items:
        print("  (empty)")
    for index, item in enumerate(items, start=1):
        marker = "READY " if item.publishable else "hold  "
        note = "" if item.publishable else f"  <- {item.skip_reason}"
        print(f"  {index}. [{marker}] {item.path.name}  {item.title or '(no title)'}{note}")

    published = state.live_records()
    print(f"\npublished ({len(published)}):")
    for record in published[-10:]:
        print(f"  {record.scheduled_at}  {record.title}  {record.post_url}")
    if not published:
        print("  (none yet)")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser."""
    parser = argparse.ArgumentParser(
        prog="ghost-publisher",
        description="Schedule queued Markdown pieces onto Ghost, one per cadence slot.",
    )
    parser.add_argument("--version", action="version", version=f"ghost-publisher {__version__}")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_ROOT / "config.yaml",
        help="path to config.yaml (default: alongside the project)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="debug-level console output")

    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="schedule the top queued piece")
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show exactly what would be sent; no API call, no file changes, no key needed",
    )
    run_parser.add_argument(
        "--force",
        action="store_true",
        help="publish even if this piece or slug looks already published (rarely correct)",
    )
    run_parser.add_argument(
        "--web-only",
        action="store_true",
        help="publish without emailing the newsletter (overrides the config default)",
    )

    sub.add_parser("status", help="show the queue, the next slot, and past publishes")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point.

    Args:
        argv: Argument vector, defaulting to `sys.argv[1:]`.

    Returns:
        A process exit code.
    """
    args = build_parser().parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"CONFIG ERROR: {exc}", file=sys.stderr)
        return EXIT_CONFIG

    configure_logging(config.paths.log_file, verbose=args.verbose)

    try:
        if args.command == "run":
            return command_run(
                config,
                dry_run=args.dry_run,
                force=args.force,
                web_only=args.web_only,
            )
        if args.command == "status":
            return command_status(config)
    except (ConfigError, StateError) as exc:
        logger.error("configuration problem: %s", exc)
        return EXIT_CONFIG
    except (QueueError, RenderError, ScheduleError) as exc:
        logger.error("cannot process the queue: %s", exc)
        return EXIT_FAILURE
    except GhostApiError as exc:
        logger.error("Ghost API error: %s", exc)
        return EXIT_FAILURE
    except Exception:  # noqa: BLE001 - unattended runs must leave a traceback
        logger.exception("unexpected failure")
        return EXIT_FAILURE

    return EXIT_FAILURE


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
