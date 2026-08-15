"""End-to-end runs against a fake Ghost. No network is ever touched."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ghost_publisher import cli
from ghost_publisher.state import State

GOOD_KEY = "0123456789abcdef01234567:" + "ab" * 32

CONFIG_YAML = """
cadence:
  every: weekly
  weekday: tuesday
  time: "09:00"
  timezone: America/New_York
  min_lead_minutes: 60
post:
  status: scheduled
  default_tags: []
  send_email: false
api:
  accept_version: "v5.0"
  timeout_seconds: 30
paths:
  queue_dir: queue
  published_dir: published
  state_file: state/published.json
  log_file: logs/run.log
"""

PIECE = """---
title: "A Real Piece"
tags:
  - Trading
feature: true
---

# Heading

Some **words** and a [link](https://example.com).
"""


class FakeGhostClient:
    """Stands in for GhostClient; records calls, invents an id."""

    instances: list[FakeGhostClient] = []

    def __init__(self, credentials, api, **_: Any) -> None:
        self.credentials = credentials
        self.api = api
        self.created: list[dict[str, Any]] = []
        self.slug_lookups: list[str] = []
        self.existing_slugs: set[str] = set()
        self.base_url = f"{credentials.api_url}/ghost/api/admin"
        FakeGhostClient.instances.append(self)

    def find_post_by_slug(self, slug: str) -> dict[str, Any] | None:
        self.slug_lookups.append(slug)
        if slug in self.existing_slugs:
            return {"id": "existing123", "slug": slug, "status": "published"}
        return None

    def create_post(
        self, payload: dict[str, Any], *, params: dict[str, str] | None = None
    ) -> dict[str, Any]:
        self.last_params = dict(params or {})
        self.created.append(payload)
        post = payload["posts"][0]
        return {
            "id": "post_abc123",
            "slug": post["slug"],
            "status": post["status"],
            "published_at": post.get("published_at"),
            "url": f"https://thomasadair.ghost.io/{post['slug']}/",
        }


@pytest.fixture
def project(tmp_path: Path, monkeypatch) -> Path:
    """A complete project directory with one ready piece in the queue."""
    monkeypatch.delenv("GHOST_ADMIN_API_KEY", raising=False)
    monkeypatch.delenv("GHOST_API_URL", raising=False)
    (tmp_path / "queue").mkdir()
    (tmp_path / "config.yaml").write_text(CONFIG_YAML)
    (tmp_path / "queue" / "01-piece.md").write_text(PIECE)
    FakeGhostClient.instances.clear()
    return tmp_path


def with_credentials(project: Path) -> None:
    (project / ".env").write_text(
        f"GHOST_ADMIN_API_KEY={GOOD_KEY}\nGHOST_API_URL=https://thomasadair.ghost.io\n"
    )


def run(project: Path, *args: str) -> int:
    return cli.main(["--config", str(project / "config.yaml"), *args])


def test_dry_run_needs_no_key_and_changes_nothing(project: Path, monkeypatch) -> None:
    monkeypatch.setattr(cli, "GhostClient", FakeGhostClient)

    assert run(project, "run", "--dry-run") == cli.EXIT_OK
    assert FakeGhostClient.instances == [], "dry run must not build a client"
    assert (project / "queue" / "01-piece.md").exists(), "queue file must stay put"
    assert not (project / "state" / "published.json").exists()
    assert not (project / "published").exists()


def test_live_run_creates_schedules_records_and_archives(
    project: Path, monkeypatch
) -> None:
    with_credentials(project)
    monkeypatch.setattr(cli, "GhostClient", FakeGhostClient)

    assert run(project, "run") == cli.EXIT_OK

    client = FakeGhostClient.instances[0]
    assert client.slug_lookups == ["a-real-piece"], "pre-flight duplicate check ran"
    assert len(client.created) == 1

    post = client.created[0]["posts"][0]
    assert post["title"] == "A Real Piece"
    assert post["status"] == "scheduled"
    assert post["slug"] == "a-real-piece"
    assert post["featured"] is True
    assert [tag["name"] for tag in post["tags"]] == ["Trading", "#field-note"]
    assert "<h1>Heading</h1>" in post["html"]
    assert "<strong>words</strong>" in post["html"]
    assert post["published_at"].endswith("Z")

    state = json.loads((project / "state" / "published.json").read_text())
    assert state["published"][0]["post_id"] == "post_abc123"
    assert state["published"][0]["source_file"] == "01-piece.md"

    assert not (project / "queue" / "01-piece.md").exists(), "should leave the queue"
    archived = list((project / "published").glob("*.md"))
    assert len(archived) == 1
    assert archived[0].name.endswith("-01-piece.md")
    assert archived[0].name[:10].count("-") == 2, "archived name is date-prefixed"


def test_second_run_refuses_to_republish_the_same_piece(
    project: Path, monkeypatch
) -> None:
    with_credentials(project)
    monkeypatch.setattr(cli, "GhostClient", FakeGhostClient)
    assert run(project, "run") == cli.EXIT_OK

    # Put the very same piece back in the queue, as a stray re-copy would.
    (project / "queue" / "01-piece.md").write_text(PIECE)
    assert run(project, "run") == cli.EXIT_REFUSED
    total_posts = sum(len(client.created) for client in FakeGhostClient.instances)
    assert total_posts == 1, "exactly one POST across both runs"
    assert (project / "queue" / "01-piece.md").exists(), "queue file left untouched"


def test_existing_slug_on_ghost_blocks_the_run(project: Path, monkeypatch) -> None:
    with_credentials(project)

    class SlugTaken(FakeGhostClient):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self.existing_slugs = {"a-real-piece"}

    monkeypatch.setattr(cli, "GhostClient", SlugTaken)
    assert run(project, "run") == cli.EXIT_REFUSED
    assert FakeGhostClient.instances[-1].created == []
    assert (project / "queue" / "01-piece.md").exists()


def test_consecutive_pieces_land_on_consecutive_weeks(
    project: Path, monkeypatch
) -> None:
    with_credentials(project)
    monkeypatch.setattr(cli, "GhostClient", FakeGhostClient)
    second = PIECE.replace("A Real Piece", "Another Piece")
    (project / "queue" / "02-piece.md").write_text(second)

    assert run(project, "run") == cli.EXIT_OK
    assert run(project, "run") == cli.EXIT_OK

    slots = [
        client.created[0]["posts"][0]["published_at"]
        for client in FakeGhostClient.instances
        if client.created
    ]
    assert len(slots) == 2
    assert slots[0] != slots[1], "two pieces must not share one slot"
    assert slots[0] < slots[1]


def test_empty_queue_is_success_not_failure(project: Path, monkeypatch) -> None:
    with_credentials(project)
    monkeypatch.setattr(cli, "GhostClient", FakeGhostClient)
    (project / "queue" / "01-piece.md").unlink()
    assert run(project, "run") == cli.EXIT_OK
    assert FakeGhostClient.instances == []


def test_queue_of_only_placeholders_publishes_nothing(
    project: Path, monkeypatch
) -> None:
    with_credentials(project)
    monkeypatch.setattr(cli, "GhostClient", FakeGhostClient)
    (project / "queue" / "01-piece.md").write_text(
        '---\ntitle: "X"\nready: false\n---\n\nPLACEHOLDER-DO-NOT-PUBLISH\n'
    )
    assert run(project, "run") == cli.EXIT_OK
    assert FakeGhostClient.instances == []


def test_live_run_without_credentials_fails_with_config_code(
    project: Path, monkeypatch
) -> None:
    monkeypatch.setattr(cli, "GhostClient", FakeGhostClient)
    assert run(project, "run") == cli.EXIT_CONFIG
    assert (project / "queue" / "01-piece.md").exists()


def test_send_email_true_is_refused_this_phase(project: Path, monkeypatch) -> None:
    with_credentials(project)
    monkeypatch.setattr(cli, "GhostClient", FakeGhostClient)
    (project / "config.yaml").write_text(
        CONFIG_YAML.replace("send_email: false", "send_email: true")
    )
    assert run(project, "run") == cli.EXIT_CONFIG
    assert FakeGhostClient.instances == []


def test_corrupt_state_file_stops_the_run(project: Path, monkeypatch) -> None:
    with_credentials(project)
    monkeypatch.setattr(cli, "GhostClient", FakeGhostClient)
    (project / "state").mkdir()
    (project / "state" / "published.json").write_text("{not json")
    assert run(project, "run") == cli.EXIT_CONFIG
    assert FakeGhostClient.instances == []


def test_shipped_queue_placeholders_are_all_held(monkeypatch) -> None:
    """Any unfilled slot in the shipped queue must never publish.

    Real pieces have since been staged into `queue/`, so the queue is no
    longer placeholder-only. The invariant that still has to hold is the
    narrow one: a file that is *still* a placeholder is never publishable,
    and any file that IS publishable carries a real title and body.
    """
    root = Path(__file__).resolve().parent.parent
    from ghost_publisher.queue import PLACEHOLDER_MARKER, list_queue

    items = list_queue(root / "queue")
    # No count assertion: the queue drains as pieces are scheduled and
    # archived, so any fixed number here goes stale. The invariant is below.
    assert items
    for item in items:
        if PLACEHOLDER_MARKER in item.path.read_text(encoding="utf-8"):
            assert not item.publishable, f"{item.path.name} is a live placeholder"
        elif item.publishable:
            assert "REPLACE WITH REAL TITLE" not in item.title
            assert item.body.strip()


def test_status_runs_without_credentials(project: Path, capsys) -> None:
    assert run(project, "status") == cli.EXIT_OK
    out = capsys.readouterr().out
    assert "NOT configured" in out
    assert "01-piece.md" in out
    assert "next slot" in out


def test_state_is_written_before_the_file_is_moved(project: Path, monkeypatch) -> None:
    """A crash during archiving must still leave a no-republish record."""
    with_credentials(project)
    monkeypatch.setattr(cli, "GhostClient", FakeGhostClient)

    def explode(*_args: Any, **_kwargs: Any) -> None:
        raise OSError("disk gone")

    monkeypatch.setattr(cli.shutil, "move", explode)
    assert run(project, "run") == cli.EXIT_FAILURE

    state = State.load(project / "state" / "published.json")
    assert len(state.live_records()) == 1, "record survives the archive failure"

    # And the next run therefore refuses rather than double-posting.
    monkeypatch.undo()
    monkeypatch.setattr(cli, "GhostClient", FakeGhostClient)
    with_credentials(project)
    assert run(project, "run") == cli.EXIT_REFUSED
