"""JWT minting, slugs, and payload shape."""

from __future__ import annotations

import base64
import json

import pytest

from ghost_publisher.config import PostDefaults
from ghost_publisher.ghost_client import (
    GhostApiError,
    build_post_payload,
    make_jwt,
    slugify,
)

KEY_ID = "0123456789abcdef01234567"
KEY_SECRET = "ab" * 32  # 64 hex chars


def _decode_segment(segment: str) -> dict:
    padded = segment + "=" * (-len(segment) % 4)
    return json.loads(base64.urlsafe_b64decode(padded))


def test_jwt_has_the_headers_and_claims_ghost_requires() -> None:
    token = make_jwt(KEY_ID, KEY_SECRET, issued_at=1_700_000_000)
    header_segment, payload_segment, signature = token.split(".")

    header = _decode_segment(header_segment)
    assert header == {"alg": "HS256", "typ": "JWT", "kid": KEY_ID}

    payload = _decode_segment(payload_segment)
    assert payload["aud"] == "/admin/"
    assert payload["iat"] == 1_700_000_000
    assert payload["exp"] == 1_700_000_300, "Ghost rejects a TTL over 5 minutes"

    assert "=" not in token, "JWS segments must be unpadded base64url"
    assert signature


def test_jwt_matches_pyjwt_when_pyjwt_is_available() -> None:
    """Cross-check the hand-rolled HMAC against a real JWT implementation."""
    jwt = pytest.importorskip("jwt")
    # A live token, so PyJWT's exp check exercises a real, unexpired lifetime.
    ours = make_jwt(KEY_ID, KEY_SECRET)

    # Decoding ours with PyJWT is the real assertion: the signature verifies.
    decoded = jwt.decode(
        ours, bytes.fromhex(KEY_SECRET), algorithms=["HS256"], audience="/admin/"
    )
    assert decoded["aud"] == "/admin/"
    assert jwt.get_unverified_header(ours)["kid"] == KEY_ID

    # Same claims as PyJWT would emit (the encodings differ only in the order
    # PyJWT serializes header keys, which is not significant to any verifier).
    theirs = jwt.encode(
        {"iat": decoded["iat"], "exp": decoded["exp"], "aud": "/admin/"},
        bytes.fromhex(KEY_SECRET),
        algorithm="HS256",
        headers={"kid": KEY_ID},
    )
    assert (
        jwt.decode(
            theirs, bytes.fromhex(KEY_SECRET), algorithms=["HS256"], audience="/admin/"
        )
        == decoded
    )

    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(ours, b"\x00" * 32, algorithms=["HS256"], audience="/admin/")


def test_non_hex_secret_fails_loudly() -> None:
    with pytest.raises(GhostApiError, match="not hex"):
        make_jwt(KEY_ID, "definitely-not-hex")


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Hello World", "hello-world"),
        ("  Spaced  Out  ", "spaced-out"),
        ("Trident Report — Week 31", "trident-report-week-31"),
        ("AP2 / x402: what it means", "ap2-x402-what-it-means"),
        ("Café Naïve Résumé", "cafe-naive-resume"),
        ("!!!", "untitled"),
    ],
)
def test_slugify(title: str, expected: str) -> None:
    assert slugify(title) == expected


def test_payload_is_shaped_the_way_the_admin_api_expects() -> None:
    payload = build_post_payload(
        title="A Piece",
        html="<p>body</p>",
        slug="a-piece",
        published_at="2026-08-04T13:00:00.000Z",
        tags=["Trading"],
        featured=True,
        excerpt="short",
        defaults=PostDefaults(status="scheduled", default_tags=["Field Notes"]),
    )
    post = payload["posts"][0]
    assert post["status"] == "scheduled"
    assert post["published_at"] == "2026-08-04T13:00:00.000Z"
    assert post["featured"] is True
    assert post["custom_excerpt"] == "short"
    assert [tag["name"] for tag in post["tags"]] == ["Field Notes", "Trading"]


def test_duplicate_tags_are_collapsed_and_ordered() -> None:
    payload = build_post_payload(
        title="T",
        html="<p>x</p>",
        slug="t",
        published_at="2026-08-04T13:00:00.000Z",
        tags=["Trading", "Field Notes"],
        featured=False,
        excerpt=None,
        defaults=PostDefaults(default_tags=["Field Notes"]),
    )
    assert [tag["name"] for tag in payload["posts"][0]["tags"]] == [
        "Field Notes",
        "Trading",
    ]


def test_draft_status_omits_published_at() -> None:
    payload = build_post_payload(
        title="T",
        html="<p>x</p>",
        slug="t",
        published_at="2026-08-04T13:00:00.000Z",
        tags=[],
        featured=False,
        excerpt=None,
        defaults=PostDefaults(status="draft"),
    )
    assert "published_at" not in payload["posts"][0]
