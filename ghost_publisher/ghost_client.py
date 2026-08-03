"""Ghost Admin API client.

Auth is a short-lived JWT signed with the secret half of the `id:secret`
Admin API key (HS256, `kid` = the id half, `aud` = "/admin/"). That is a dozen
lines of stdlib HMAC, so there is no PyJWT dependency here.

Only two calls are ever made:
  * GET  /posts/slug/{slug}/   — read-only pre-flight duplicate check
  * POST /posts/?source=html   — create the scheduled post
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import re
import time
import unicodedata
from typing import Any

import requests

from .config import ApiSettings, Credentials, PostDefaults

logger = logging.getLogger(__name__)

TOKEN_TTL_SECONDS = 300  # Ghost rejects tokens with a lifetime over 5 minutes.
ADMIN_API_PATH = "/ghost/api/admin"
MAX_SLUG_LENGTH = 185


class GhostApiError(Exception):
    """Raised when Ghost rejects a request or is unreachable."""


def _b64url(data: bytes) -> str:
    """Base64url-encode without padding, per JWS."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def make_jwt(key_id: str, key_secret: str, *, issued_at: int | None = None) -> str:
    """Mint a Ghost Admin API JWT.

    Args:
        key_id: The `id` half of the Admin API key (becomes the `kid` header).
        key_secret: The `secret` half, hex-encoded.
        issued_at: Override for `iat`, in epoch seconds. Testing hook.

    Returns:
        The signed compact JWS string.

    Raises:
        GhostApiError: `key_secret` is not valid hex.
    """
    try:
        secret_bytes = bytes.fromhex(key_secret)
    except ValueError as exc:
        raise GhostApiError(
            "the secret half of GHOST_ADMIN_API_KEY is not hex — "
            "re-copy the Admin API key from Ghost"
        ) from exc

    iat = int(time.time()) if issued_at is None else int(issued_at)
    header = {"alg": "HS256", "typ": "JWT", "kid": key_id}
    payload = {"iat": iat, "exp": iat + TOKEN_TTL_SECONDS, "aud": "/admin/"}

    segments = [
        _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8")),
        _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
    ]
    signing_input = ".".join(segments).encode("ascii")
    signature = hmac.new(secret_bytes, signing_input, hashlib.sha256).digest()
    segments.append(_b64url(signature))
    return ".".join(segments)


def slugify(title: str) -> str:
    """Derive a URL slug from a title, the way Ghost would.

    Sending an explicit slug matters: if Ghost generates one and it collides,
    it silently appends `-2` and we get a duplicate post instead of an error.

    Args:
        title: The post title.

    Returns:
        A lowercase hyphenated slug.
    """
    normalized = unicodedata.normalize("NFKD", title)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_only).strip("-").lower()
    slug = re.sub(r"-{2,}", "-", slug)
    return slug[:MAX_SLUG_LENGTH].strip("-") or "untitled"


def build_post_payload(
    *,
    title: str,
    html: str,
    slug: str,
    published_at: str,
    tags: list[str],
    featured: bool,
    excerpt: str | None,
    defaults: PostDefaults,
) -> dict[str, Any]:
    """Assemble the Admin API request body for a new post.

    Args:
        title: Post title.
        html: Rendered post body.
        slug: Explicit slug.
        published_at: ISO-8601 UTC slot timestamp.
        tags: Per-piece tag names.
        featured: Whether to feature the post.
        excerpt: Optional custom excerpt.
        defaults: Config-level post defaults.

    Returns:
        The `{"posts": [...]}` request body.
    """
    all_tags = list(dict.fromkeys([*defaults.default_tags, *tags]))
    post: dict[str, Any] = {
        "title": title,
        "slug": slug,
        "html": html,
        "status": defaults.status,
        "featured": featured,
    }
    if defaults.status == "scheduled":
        post["published_at"] = published_at
    if all_tags:
        post["tags"] = [{"name": name} for name in all_tags]
    if excerpt:
        post["custom_excerpt"] = excerpt
    return {"posts": [post]}


class GhostClient:
    """Thin, explicit wrapper over the two Admin API endpoints we use."""

    def __init__(
        self,
        credentials: Credentials,
        api: ApiSettings,
        *,
        session: requests.Session | None = None,
    ) -> None:
        """Create a client.

        Args:
            credentials: Validated Ghost credentials.
            api: Transport settings (version header, timeout).
            session: Optional injected `requests.Session`, for tests.
        """
        self.credentials = credentials
        self.api = api
        self.session = session or requests.Session()

    @property
    def base_url(self) -> str:
        """Root URL of the Admin API, no trailing slash."""
        return f"{self.credentials.api_url}{ADMIN_API_PATH}"

    def _headers(self) -> dict[str, str]:
        """Auth and version headers for a single request."""
        token = make_jwt(self.credentials.key_id, self.credentials.key_secret)
        return {
            "Authorization": f"Ghost {token}",
            "Accept-Version": self.api.accept_version,
            "Content-Type": "application/json",
            "User-Agent": "ghost-publisher/0.1",
        }

    @staticmethod
    def _describe_error(response: requests.Response) -> str:
        """Turn a Ghost error response into a one-line message."""
        try:
            body = response.json()
            errors = body.get("errors") or []
            parts = [
                f"{err.get('message', '?')}"
                + (f" ({err.get('context')})" if err.get("context") else "")
                for err in errors
            ]
            detail = "; ".join(parts) if parts else json.dumps(body)[:400]
        except ValueError:
            detail = response.text[:400]
        return f"HTTP {response.status_code}: {detail}"

    def find_post_by_slug(self, slug: str) -> dict[str, Any] | None:
        """Look up an existing post by slug. Read-only.

        Args:
            slug: The slug to check.

        Returns:
            The post dict if one exists, otherwise None.

        Raises:
            GhostApiError: The request failed for any reason other than 404.
        """
        url = f"{self.base_url}/posts/slug/{slug}/"
        try:
            response = self.session.get(
                url,
                headers=self._headers(),
                params={"fields": "id,slug,status,published_at,url"},
                timeout=self.api.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise GhostApiError(f"could not reach Ghost at {url}: {exc}") from exc

        if response.status_code == 404:
            return None
        if not response.ok:
            raise GhostApiError(
                f"slug lookup failed — {self._describe_error(response)}"
            )
        posts = response.json().get("posts") or []
        return posts[0] if posts else None

    def create_post(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a post from HTML source.

        Args:
            payload: Body from `build_post_payload`.

        Returns:
            The created post dict as returned by Ghost.

        Raises:
            GhostApiError: The request failed or the response was unexpected.
        """
        url = f"{self.base_url}/posts/"
        try:
            response = self.session.post(
                url,
                headers=self._headers(),
                params={"source": "html"},
                json=payload,
                timeout=self.api.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise GhostApiError(f"could not reach Ghost at {url}: {exc}") from exc

        if not response.ok:
            raise GhostApiError(
                f"post creation failed — {self._describe_error(response)}"
            )

        try:
            posts = response.json()["posts"]
            return posts[0]
        except (ValueError, KeyError, IndexError) as exc:
            raise GhostApiError(
                f"Ghost returned an unexpected body: {response.text[:400]}"
            ) from exc
