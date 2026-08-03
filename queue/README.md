# The queue

Drop finished Markdown pieces in this folder. They go out **top to bottom, one
per cadence slot** (default: one per week, Tuesday 09:00).

Order is filename order, which is why files are numbered. To move something up
the queue, renumber it — `05-…` becomes `00-…` and it goes next.

## Adding a piece

1. Create a file here: `05-my-piece.md` (any name; the number sets the order).
2. Start it with a frontmatter block, then write in Markdown:

```markdown
---
title: "The real headline of the piece"
tags:
  - Trading
  - Field Notes
feature: false
---

Your piece starts here. Normal Markdown — headings, **bold**, links,
`code`, lists, tables, images.
```

3. That's it. The next scheduled run picks up the top file.

## Frontmatter fields

| Field | Required | Default | What it does |
|---|---|---|---|
| `title` | **yes** | — | The post title on Ghost |
| `tags` | no | none | List of Ghost tags; created if they don't exist |
| `feature` | no | `false` | `true` marks the post as featured |
| `ready` | no | `true` | `false` holds the file back — the run skips it |
| `slug` | no | from title | Override the URL slug |
| `excerpt` | no | none | Custom excerpt shown in cards/previews |

Anything held back (`ready: false`, no title, empty body, or still containing
the `PLACEHOLDER-DO-NOT-PUBLISH` marker) is skipped with a logged reason and
the run moves to the next file. It is not an error.

## What's here now

`01`–`04` are the four finished articles, staged in the locked publication
order and marked `ready: true`:

- `01-persistent-memory-bundle.md` — The Persistent Memory Bundle
- `02-expected-outcome-reframe.md` — The Expected Outcome Reframe
- `03-adversarial-dynamical-systems.md` — Adversarial Dynamical Systems
- `04-ap2-x402-kill-path.md` — The Kill Path Shares Fate with the Pay Path

`10-trident-report.md` and `11-london-kz.md` are still **empty placeholders**
for pieces that have not been written — instructions, not content. They sit
below the ready four and are skipped on every run. Paste the real piece in, fix
the title, flip `ready: true`, and renumber to move it up the order.

## After a piece publishes

The file moves to `../published/` with the slot date prefixed, e.g.
`published/2026-08-04-01-trident-report.md`, and a record lands in
`../state/published.json`. Both exist so the same piece can never go out twice.
