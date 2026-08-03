"""Queue parsing, credential validation, and the placeholder safety net."""

from __future__ import annotations

from pathlib import Path

import pytest

from ghost_publisher.config import (
    ConfigError,
    load_config,
    load_credentials,
    parse_env_file,
)
from ghost_publisher.queue import (
    QueueError,
    list_queue,
    load_item,
    next_publishable,
    split_frontmatter,
)

GOOD_KEY = "0123456789abcdef01234567:" + "ab" * 32


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_frontmatter_splits_cleanly() -> None:
    front, body = split_frontmatter(
        '---\ntitle: "T"\ntags: [a, b]\n---\n\nBody here.\n'
    )
    assert front == {"title": "T", "tags": ["a", "b"]}
    assert body.strip() == "Body here."


def test_file_without_frontmatter_is_all_body() -> None:
    front, body = split_frontmatter("# Just a heading\n")
    assert front == {}
    assert body.startswith("# Just")


def test_broken_frontmatter_raises() -> None:
    with pytest.raises(QueueError):
        split_frontmatter("---\ntitle: [unclosed\n---\nbody\n")


def test_minimal_item_needs_only_a_title(tmp_path: Path) -> None:
    path = write(tmp_path / "05-x.md", '---\ntitle: "Hello"\n---\n\nSome words.\n')
    item = load_item(path)
    assert item.publishable
    assert item.title == "Hello"
    assert item.ready is True, "a file with no `ready` key is ready"
    assert item.tags == []
    assert item.featured is False


def test_tags_accept_a_comma_separated_string(tmp_path: Path) -> None:
    path = write(tmp_path / "a.md", '---\ntitle: "T"\ntags: "one, two"\n---\n\nBody\n')
    assert load_item(path).tags == ["one", "two"]


def test_feature_flag_is_read(tmp_path: Path) -> None:
    path = write(tmp_path / "a.md", '---\ntitle: "T"\nfeature: true\n---\n\nBody\n')
    assert load_item(path).featured is True


@pytest.mark.parametrize(
    ("text", "fragment"),
    [
        ('---\ntitle: "T"\nready: false\n---\n\nBody\n', "ready: false"),
        ('---\ntitle: ""\n---\n\nBody\n', "no title"),
        ('---\ntitle: "T"\n---\n\n\n', "empty"),
        ('---\ntitle: "T"\n---\n\nPLACEHOLDER-DO-NOT-PUBLISH\n', "placeholder"),
    ],
)
def test_unfinished_items_are_held_not_published(
    tmp_path: Path, text: str, fragment: str
) -> None:
    item = load_item(write(tmp_path / "a.md", text))
    assert not item.publishable
    assert fragment in item.skip_reason


def test_placeholder_beats_a_ready_true_flag(tmp_path: Path) -> None:
    """The marker wins even if `ready` was flipped by mistake."""
    path = write(
        tmp_path / "a.md",
        '---\ntitle: "T"\nready: true\n---\n\nPLACEHOLDER-DO-NOT-PUBLISH\n\nreal-ish text\n',
    )
    assert not load_item(path).publishable


def test_queue_is_processed_in_filename_order(tmp_path: Path) -> None:
    for name in ("03-c.md", "01-a.md", "02-b.md"):
        write(tmp_path / name, f'---\ntitle: "{name}"\n---\n\nBody\n')
    assert [item.path.name for item in list_queue(tmp_path)] == [
        "01-a.md",
        "02-b.md",
        "03-c.md",
    ]


def test_next_publishable_skips_held_items(tmp_path: Path) -> None:
    write(tmp_path / "01-hold.md", '---\ntitle: "H"\nready: false\n---\n\nBody\n')
    write(tmp_path / "02-go.md", '---\ntitle: "G"\n---\n\nBody\n')
    assert next_publishable(list_queue(tmp_path)).title == "G"


def test_queue_readme_is_not_treated_as_content(tmp_path: Path) -> None:
    write(tmp_path / "README.md", "# instructions\n")
    write(tmp_path / "01-a.md", '---\ntitle: "A"\n---\n\nBody\n')
    assert [item.path.name for item in list_queue(tmp_path)] == ["01-a.md"]


def test_one_broken_file_does_not_block_the_rest(tmp_path: Path) -> None:
    write(tmp_path / "01-broken.md", "---\ntitle: [oops\n---\nbody\n")
    write(tmp_path / "02-fine.md", '---\ntitle: "Fine"\n---\n\nBody\n')
    items = list_queue(tmp_path)
    assert [item.title for item in items] == ["Fine"]


def test_content_hash_tracks_content_not_filename(tmp_path: Path) -> None:
    text = '---\ntitle: "Same"\n---\n\nIdentical body.\n'
    first = load_item(write(tmp_path / "01-a.md", text))
    second = load_item(write(tmp_path / "09-renamed.md", text))
    assert first.content_hash == second.content_hash


def test_env_parsing_handles_export_quotes_and_comments() -> None:
    parsed = parse_env_file(
        '# a comment\nexport GHOST_API_URL="https://x.ghost.io"\n\nKEY=plain\n'
    )
    assert parsed["GHOST_API_URL"] == "https://x.ghost.io"
    assert parsed["KEY"] == "plain"


def test_valid_credentials_split_into_id_and_secret(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.delenv("GHOST_ADMIN_API_KEY", raising=False)
    monkeypatch.delenv("GHOST_API_URL", raising=False)
    env = write(
        tmp_path / ".env",
        f"GHOST_ADMIN_API_KEY={GOOD_KEY}\nGHOST_API_URL=https://thomasadair.ghost.io/\n",
    )
    creds = load_credentials(env, required=True)
    assert creds.key_id == "0123456789abcdef01234567"
    assert len(creds.key_secret) == 64
    assert creds.api_url == "https://thomasadair.ghost.io", "trailing slash trimmed"


@pytest.mark.parametrize(
    ("key", "url", "fragment"),
    [
        ("REPLACE_WITH_ID:REPLACE_WITH_SECRET", "https://x.ghost.io", "not set"),
        ("short:key", "https://x.ghost.io", "malformed"),
        (GOOD_KEY, "x.ghost.io", "https://"),
        (GOOD_KEY, "https://x.ghost.io/ghost/api/admin", "site root"),
    ],
)
def test_bad_credentials_are_rejected_with_a_useful_message(
    tmp_path: Path, monkeypatch, key: str, url: str, fragment: str
) -> None:
    monkeypatch.delenv("GHOST_ADMIN_API_KEY", raising=False)
    monkeypatch.delenv("GHOST_API_URL", raising=False)
    env = write(tmp_path / ".env", f"GHOST_ADMIN_API_KEY={key}\nGHOST_API_URL={url}\n")
    with pytest.raises(ConfigError, match=fragment):
        load_credentials(env, required=True)
    assert load_credentials(env, required=False) is None, "dry-run must not raise"


def test_missing_env_file_is_survivable_for_dry_run(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.delenv("GHOST_ADMIN_API_KEY", raising=False)
    monkeypatch.delenv("GHOST_API_URL", raising=False)
    assert load_credentials(tmp_path / "nope.env", required=False) is None


def test_shipped_config_yaml_is_valid() -> None:
    config = load_config(Path(__file__).resolve().parent.parent / "config.yaml")
    assert config.cadence.every == "weekly"
    assert config.cadence.weekday == "tuesday"
    assert config.cadence.time == "09:00"
    assert config.post.status == "scheduled"
    assert config.post.send_email is False


def test_invalid_cadence_values_are_rejected(tmp_path: Path) -> None:
    path = write(tmp_path / "config.yaml", "cadence:\n  every: hourly\n")
    with pytest.raises(ConfigError, match="cadence.every"):
        load_config(path)

    path = write(tmp_path / "config.yaml", "cadence:\n  weekday: someday\n")
    with pytest.raises(ConfigError, match="weekday"):
        load_config(path)

    path = write(tmp_path / "config.yaml", 'cadence:\n  time: "9am"\n')
    with pytest.raises(ConfigError, match="time"):
        load_config(path)

    path = write(tmp_path / "config.yaml", 'cadence:\n  time: "25:00"\n')
    with pytest.raises(ConfigError, match="range"):
        load_config(path)
