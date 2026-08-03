"""Configuration and environment loading.

Two separate sources, deliberately:
  * `config.yaml` — cadence and post defaults. Committed, no secrets.
  * `.env`        — GHOST_ADMIN_API_KEY and GHOST_API_URL. Never committed.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# <24 hex>:<64 hex> — the shape Ghost hands out for an Admin API key.
ADMIN_KEY_RE = re.compile(r"^[0-9a-fA-F]{24}:[0-9a-fA-F]{64}$")

VALID_CADENCES = ("weekly", "biweekly", "daily")
WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


class ConfigError(Exception):
    """Raised when config.yaml or .env is missing or malformed."""


@dataclass(frozen=True)
class Cadence:
    """When the next publish slot falls."""

    every: str = "weekly"
    weekday: str = "tuesday"
    time: str = "09:00"
    timezone: str = "local"
    min_lead_minutes: int = 60

    @property
    def weekday_index(self) -> int:
        """Monday=0 ... Sunday=6, matching `datetime.weekday()`."""
        return WEEKDAYS[self.weekday.lower()]

    @property
    def hour_minute(self) -> tuple[int, int]:
        """Parse `time` into (hour, minute)."""
        hour_str, _, minute_str = self.time.partition(":")
        return int(hour_str), int(minute_str)

    @property
    def interval_days(self) -> int:
        """How far apart two consecutive slots are."""
        return {"weekly": 7, "biweekly": 14, "daily": 1}[self.every]


@dataclass(frozen=True)
class PostDefaults:
    """Defaults applied to every created post."""

    status: str = "scheduled"
    default_tags: list[str] = field(default_factory=list)
    send_email: bool = False


@dataclass(frozen=True)
class ApiSettings:
    """Ghost Admin API transport settings."""

    accept_version: str = "v5.0"
    timeout_seconds: int = 30


@dataclass(frozen=True)
class Paths:
    """Filesystem layout, resolved to absolute paths against the project root."""

    root: Path
    queue_dir: Path
    published_dir: Path
    state_file: Path
    log_file: Path


@dataclass(frozen=True)
class Config:
    """Full resolved configuration for a run."""

    cadence: Cadence
    post: PostDefaults
    api: ApiSettings
    paths: Paths


@dataclass(frozen=True)
class Credentials:
    """Ghost Admin API credentials read from `.env`."""

    admin_api_key: str
    api_url: str

    @property
    def key_id(self) -> str:
        """The `id` half of the `id:secret` Admin API key."""
        return self.admin_api_key.split(":", 1)[0]

    @property
    def key_secret(self) -> str:
        """The `secret` (hex) half of the `id:secret` Admin API key."""
        return self.admin_api_key.split(":", 1)[1]


def load_config(config_path: Path) -> Config:
    """Read and validate `config.yaml`.

    Args:
        config_path: Path to the YAML config file.

    Returns:
        A fully populated, validated `Config`.

    Raises:
        ConfigError: The file is missing, unreadable, or has invalid values.
    """
    if not config_path.exists():
        raise ConfigError(f"config file not found: {config_path}")

    try:
        raw: dict[str, Any] = yaml.safe_load(config_path.read_text()) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"config file is not valid YAML: {exc}") from exc

    cadence = Cadence(**(raw.get("cadence") or {}))
    if cadence.every not in VALID_CADENCES:
        raise ConfigError(
            f"cadence.every must be one of {VALID_CADENCES}, got {cadence.every!r}"
        )
    if cadence.weekday.lower() not in WEEKDAYS:
        raise ConfigError(
            f"cadence.weekday must be a day name, got {cadence.weekday!r}"
        )
    if not re.fullmatch(r"\d{1,2}:\d{2}", cadence.time):
        raise ConfigError(f'cadence.time must be "HH:MM", got {cadence.time!r}')
    hour, minute = cadence.hour_minute
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ConfigError(f"cadence.time is out of range: {cadence.time!r}")
    if cadence.min_lead_minutes < 0:
        raise ConfigError("cadence.min_lead_minutes must be >= 0")

    post = PostDefaults(**(raw.get("post") or {}))
    if post.status not in ("scheduled", "draft"):
        raise ConfigError(
            f'post.status must be "scheduled" or "draft", got {post.status!r}'
        )

    api = ApiSettings(**(raw.get("api") or {}))

    root = config_path.parent.resolve()
    raw_paths = raw.get("paths") or {}
    paths = Paths(
        root=root,
        queue_dir=root / raw_paths.get("queue_dir", "queue"),
        published_dir=root / raw_paths.get("published_dir", "published"),
        state_file=root / raw_paths.get("state_file", "state/published.json"),
        log_file=root / raw_paths.get("log_file", "logs/run.log"),
    )

    return Config(cadence=cadence, post=post, api=api, paths=paths)


def parse_env_file(text: str) -> dict[str, str]:
    """Parse a minimal `.env` file body into a dict.

    Supports `KEY=value`, `export KEY=value`, `#` comments, blank lines, and
    optional surrounding single or double quotes. Deliberately tiny — there is
    no dependency on python-dotenv.

    Args:
        text: Raw contents of a `.env` file.

    Returns:
        Mapping of environment key to value.
    """
    values: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[len("export ") :].strip()
        key, sep, value = stripped.partition("=")
        if not sep:
            continue
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key] = value
    return values


def load_credentials(env_path: Path, *, required: bool = True) -> Credentials | None:
    """Load Ghost credentials from `.env`, falling back to the process env.

    Values already present in `os.environ` win over the file, so a launchd or
    CI environment can override without editing files.

    Args:
        env_path: Path to the `.env` file.
        required: When False, return None instead of raising if the key is
            missing or malformed. Used by `--dry-run`, which never calls Ghost.

    Returns:
        `Credentials`, or None when `required` is False and they are unusable.

    Raises:
        ConfigError: `required` is True and the credentials are missing or
            malformed.
    """
    file_values: dict[str, str] = {}
    if env_path.exists():
        file_values = parse_env_file(env_path.read_text())
    else:
        logger.debug("no .env file at %s; using process environment only", env_path)

    key = os.environ.get("GHOST_ADMIN_API_KEY") or file_values.get(
        "GHOST_ADMIN_API_KEY", ""
    )
    url = os.environ.get("GHOST_API_URL") or file_values.get("GHOST_API_URL", "")
    key = key.strip()
    url = url.strip().rstrip("/")

    problems: list[str] = []
    if not key or key.startswith("REPLACE_WITH"):
        problems.append(
            "GHOST_ADMIN_API_KEY is not set (copy env.example to .env and paste "
            "the Admin API key from Ghost -> Settings -> Integrations)"
        )
    elif not ADMIN_KEY_RE.match(key):
        problems.append(
            "GHOST_ADMIN_API_KEY is malformed — expected <24 hex>:<64 hex>. "
            "Check you copied the Admin API key, not the Content API key."
        )
    if not url:
        problems.append("GHOST_API_URL is not set (e.g. https://thomasadair.ghost.io)")
    elif not url.startswith(("http://", "https://")):
        problems.append(f"GHOST_API_URL must start with https:// — got {url!r}")
    elif "/ghost/api" in url:
        problems.append(
            f"GHOST_API_URL must be the site root only, not an API path — got {url!r}"
        )

    if problems:
        if not required:
            logger.warning(
                "credentials unusable (fine for --dry-run): %s", "; ".join(problems)
            )
            return None
        raise ConfigError("; ".join(problems))

    return Credentials(admin_api_key=key, api_url=url)
