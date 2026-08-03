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

## The four seeded slots

`01`–`04` are **empty placeholders** for pieces that already exist elsewhere:

- `01-trident-report.md` — Trident Report / Digest
- `02-ap2-x402-essay.md` — AP2 / x402 essay
- `03-london-kz.md` — London-KZ
- `04-memory-bundle-guide.md` — Memory Bundle Guide

Each one contains instructions, not content. Nothing was written for you. Paste
the real piece in, fix the title, flip `ready: true`.

## After a piece publishes

The file moves to `../published/` with the slot date prefixed, e.g.
`published/2026-08-04-01-trident-report.md`, and a record lands in
`../state/published.json`. Both exist so the same piece can never go out twice.
