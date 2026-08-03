# ghost-publisher

Drop finished Markdown into `queue/`. A weekly job takes the top piece, renders
it, and creates it on **Ghost** (`https://thomasadair.ghost.io`) as a
*scheduled* post. Ghost publishes it server-side at the slot time.

You write. Everything else — formatting, date-picking, publishing — is automated.

**Default cadence: one piece per week, Tuesday 09:00 local.**

Web-only for this phase: no newsletter/email send. That is a deliberate choice,
not a limitation — Ghost lets you add email to any individual post later without
changing anything here.

---

## Setup (once)

```bash
cd ~/projects/p2-utilities/ghost-publisher

# 1. Dependencies (a local virtualenv; run.sh picks it up automatically)
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. Credentials
cp env.example .env
#    then open .env and paste your Ghost Admin API key

# 3. Check it
./run.sh status
```

### The `.env` format

`.env` lives in the project root and holds exactly two lines:

```
GHOST_ADMIN_API_KEY=<24-hex-id>:<64-hex-secret>
GHOST_API_URL=https://thomasadair.ghost.io
```

The shape of the key, spelled out rather than written as plausible hex (so no
scanner mistakes this README for a leak):

```
GHOST_ADMIN_API_KEY=<24 hex chars><colon><64 hex chars>
                     ^^^^^^^^^^^^^       ^^^^^^^^^^^^^
                     the "id" half        the "secret" half
```

One line, one colon, no spaces, no quotes.

Where the key comes from: **Ghost admin → Settings → Advanced → Integrations →
Add custom integration** (name it `ghost-publisher`) → copy the **Admin API
key**. Not the Content API key. It is one string with a colon in the middle;
paste it whole, no quotes.

`GHOST_API_URL` is the site root only — no trailing slash, no `/ghost/api/...`
path. The script appends the API path itself and will tell you if you get this
wrong.

`.env` is git-ignored and never committed. `env.example` is the committed
template. (It is named `env.example` rather than `.env.example` because this
Mac has a safety hook that blocks agents from writing any `.env*` file.)

---

## Adding a piece to the queue

Create a file in `queue/`. The filename number sets the order — lowest goes out
next.

```markdown
---
title: "The real headline"
tags:
  - Trading
  - Field Notes
feature: false
---

Your piece here, in normal Markdown.
```

| Field | Required | Default | Effect |
|---|---|---|---|
| `title` | **yes** | — | Post title on Ghost |
| `tags` | no | none | Ghost tags; created if new |
| `feature` | no | `false` | `true` = featured post |
| `ready` | no | `true` | `false` holds the piece back |
| `slug` | no | from title | Override the URL slug |
| `excerpt` | no | none | Custom excerpt for cards/previews |

That's the whole interface. See `queue/README.md` for more detail.

### What's in the queue

`queue/01`–`04` hold the four finished articles, staged in the locked
publication order and marked `ready: true`:

| File | Piece | Source of record |
|---|---|---|
| `01-persistent-memory-bundle.md` | The Persistent Memory Bundle | `trident-forge/docs/publishing/memory_bundle_ghost_ready.md` |
| `02-expected-outcome-reframe.md` | The Expected Outcome Reframe | `trident-forge/docs/publishing/article2_expected_outcome_reframe.md` |
| `03-adversarial-dynamical-systems.md` | Adversarial Dynamical Systems | `trident-forge/docs/publishing/article3_adversarial_dynamical_systems.md` |
| `04-ap2-x402-kill-path.md` | The Kill Path Shares Fate with the Pay Path | `trident_report_ap2_x402_piece_v0.2.md` (2026-07-26 byline + D2 pass) |

Each holds the reader-facing body only — the change logs, draft notes, and
draft-meta blocks that live in the source files are editorial apparatus and
stay behind.

`queue/10-trident-report.md` and `queue/11-london-kz.md` are still **empty
placeholders** for pieces that have not been written. They sit below the ready
four and are skipped on every run. To use one: delete the comment block, paste
the piece, fix `title:`, set `ready: true`, and renumber it to where you want
it in the order.

---

## Running it

```bash
./run.sh status            # queue, next slot, what's already gone out
./run.sh run --dry-run     # full rehearsal — no API call, no key needed
./run.sh run               # schedule the top piece for real
```

**Dry run** does everything except talk to Ghost: picks the piece, renders the
HTML, computes the slot, prints the exact payload. It works with no `.env` at
all, and touches no files. Use it whenever you want to see what's next.

Exit codes: `0` success or nothing to do · `1` failure · `2` config/credential
problem · `3` refused for safety.

### What one run does

1. Reads `queue/` in filename order, skipping anything held back.
2. Takes the top ready piece.
3. Computes the next cadence slot — always later than now *and* later than the
   last slot already given to Ghost, so two pieces never collide.
4. Renders Markdown → HTML, and creates the post with `status: scheduled` and
   that `published_at`. **Ghost does the actual publishing, server-side.** Your
   Mac does not need to be awake at 09:00 Tuesday.
5. Writes a record to `state/published.json`, then moves the file to
   `published/2026-08-04-01-piece.md`.

### Never publishing twice

Four independent guards:

- `state/published.json` records every post; a matching filename **or** content
  hash refuses the run (exit 3).
- Published files leave `queue/` entirely.
- Before creating, it asks Ghost whether the slug already exists — if so it
  refuses rather than letting Ghost silently make a `-2` duplicate.
- State is written *before* the file is moved, so a crash mid-run still leaves
  the "already published" record.

`--force` overrides the first and third. You will almost never want it.

---

## Cadence

Edit `config.yaml`:

```yaml
cadence:
  every: weekly          # weekly | biweekly | daily
  weekday: tuesday
  time: "09:00"
  timezone: local        # or America/New_York, Europe/London, ...
  min_lead_minutes: 60   # never schedule a slot closer than this
```

Wall-clock times are honoured across daylight-saving changes — 09:00 stays
09:00, and the UTC timestamp sent to Ghost shifts accordingly.

`post.status` can be set to `draft` if you ever want a human gate instead of
auto-scheduling. `post.send_email` must stay `false` this phase; the run refuses
with a clear message if you flip it.

---

## The weekly trigger

```bash
./scripts/install-launchd.sh     # enable
./scripts/uninstall-launchd.sh   # disable
```

That installs a launchd user agent at
`~/Library/LaunchAgents/com.thomasadair.ghost-publisher.plist` running:

**every Monday 08:00 local** → `./run.sh run`

Monday 08:00 schedules the top piece for Tuesday 09:00 — about 25 hours of lead,
comfortably above `min_lead_minutes`. If the Mac is asleep at 08:00, launchd
runs the job once on the next wake.

Useful commands:

```bash
launchctl print gui/$UID/com.thomasadair.ghost-publisher | head -20   # is it loaded?
launchctl kickstart -p gui/$UID/com.thomasadair.ghost-publisher       # run it now
tail -f logs/run.log                                                  # watch it
```

### cron instead

If you'd rather use cron, skip the installer and add this line to `crontab -e`
(same Monday 08:00 slot):

```cron
0 8 * * 1 /Users/thomasadair/projects/p2-utilities/ghost-publisher/run.sh run >> /Users/thomasadair/projects/p2-utilities/ghost-publisher/logs/cron.log 2>&1
```

launchd is the better choice on macOS — cron does not catch up on missed runs
while the Mac is asleep.

---

## Layout

```
ghost-publisher/
├── env.example              template → copy to .env, paste key there
├── config.yaml              cadence and post defaults (no secrets)
├── run.sh                   launcher (used by launchd/cron)
├── requirements.txt
├── queue/                   ← you drop Markdown here
│   ├── README.md
│   └── 01..04-*.md          placeholders for the four ready pieces
├── published/               pieces that have gone out (auto-moved)
├── state/published.json     no-republish ledger (git-ignored)
├── logs/                    run logs, rotated (git-ignored)
├── scripts/                 launchd plist + install/uninstall
├── ghost_publisher/         the code
│   ├── cli.py               orchestration and exit codes
│   ├── config.py            config.yaml + .env loading and validation
│   ├── queue.py             frontmatter parsing, ordering, hold rules
│   ├── scheduling.py        slot arithmetic (timezone/DST aware)
│   ├── render.py            Markdown → HTML
│   ├── ghost_client.py      Admin API JWT auth + the two API calls
│   ├── state.py             the published ledger
│   └── logging_setup.py
└── tests/                   64 tests, no network
```

## Tests

```bash
.venv/bin/python -m pytest tests/ -q
```

No test touches the network. The Ghost client is faked, so the full live path —
create, record, archive, refuse-on-repeat — is exercised without a key.

## Notes

- **Ghost format**: posts are created with `?source=html`, so Ghost converts the
  HTML to its own Lexical format server-side. Nothing here has to know about
  Lexical or Mobiledoc, which is what keeps the project small.
- **Auth**: the Admin API needs a short-lived JWT signed with the secret half of
  the key. That's a dozen lines of stdlib HMAC in `ghost_client.py` — no PyJWT
  dependency at runtime (the test suite cross-checks against PyJWT when it's
  installed).
- **Related**: `~/projects/publishing-pipeline` is an older scaffold-only repo
  for the same idea (spec written, no implementation). This project supersedes
  it for actually publishing. If you want the `publish.event.v1` Hermes event
  emission described there, that's a follow-on to wire in.
