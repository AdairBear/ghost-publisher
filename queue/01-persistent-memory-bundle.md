---
title: "The Persistent Memory Bundle"
slug: "persistent-memory-bundle"
excerpt: "How I keep Claude coherent across model swaps, session death, and long gaps — three layers, months of survival, and the discipline that makes them work."
tags:
  - AI
  - solo-builder
  - field-notes
  - systems-architecture
  - memory
feature: false
ready: true
---

**By Thomas Adair.** Marine. DJ/Producer. Systems Architect — shipping across trading systems, music production, agentic tooling, and consumer apps with AI orchestration.

*How I keep Claude coherent across model swaps, session death, and long gaps — the substrate everything else in my workflow sits on top of.*

---

A friend got me interested in day trading in August of 2025. He pitched it the way everyone pitches it — learn this and you can replace your paycheck — the same rigamarole the course sellers run. I had always been somewhat interested anyway. At the same time, by happenstance, I was learning that people were using AI to write real software. I had never built a program in my life, unless you count a self-hosted Pac-Man clone I made for my kids.

The two converged. When I found out you could write a strategy in Pine Script, wire it through TradersPost into a prop firm account, and let it trade, a very large lightbulb went off.

None of it was agentic. My actual process was: open a chat, explain everything from the beginning, get some code, close the chat, lose everything, do it again tomorrow. When the community tore open around OpenClaw I tried it, then MoltBot, then Hermes, which stuck. Every time the tooling changed, the thing I lost was the same — everything the last version of me had worked out.

I have spent the past year building a live-money trading system and the AI substrate around it. No revenue yet. I would rather it prove itself before I decide what it becomes. The single most important architectural decision I made along the way is that memory does not live inside the model.

Not inside the current session. Not inside the chat window. Not inside whichever context length the vendor is advertising this quarter. Memory lives in files I own, on infrastructure I control, updated on a discipline, and consulted by every session that opens on my machine or my server.

Three layers. Months of operation, hundreds of session terminations, dozens of model rotations, laptop closures across weeks-long gaps, one VPS reboot cycle. What follows is what each layer is and what forced it into existence.

## Layer one — the local memory bundle

The first layer is a directory of Markdown files under `~/agent/memory/`.

```
~/agent/memory/
├── MEMORY.md              # the index
├── user_writing_voice.md
├── feedback_confidence_tagging.md
├── feedback_topstep_blown.md
├── project_trident_forge.md
├── project_open_orchestra.md
├── reference_karpathy_claude_md.md
├── notes_agentic_design_patterns_ch11.md
├── audit_gap_verification_2026-06-25.md
└── … about two hundred more files
```

I did not invent this shape. Andrej Karpathy published a pattern for an LLM wiki — an index file, a set of small linked articles, wikilinks between them — and that gist is the direct ancestor of what sits on my disk. There is a real difference between taking someone's work and taking someone's idea and building your own thing on it. This is the second one. Credit where credit is due.

What I changed was the typing, and I changed it because my failures were typed. "The model forgot something" was never one problem. Forgetting who I am, forgetting a correction, forgetting where a build stands, and forgetting a paper I meant to keep are four different failures, and they have to be findable by kind. So each file carries front-matter with a `type`, and the types are the failure classes. **User** memories hold who I am and how I want to be spoken to. **Feedback** memories hold corrections I do not want to give twice. **Project** memories hold the state of a build in flight. **Reference** memories hold papers and repos with my note about *why* each one matters. **Notes and audits** hold the thinking work.

Every file has one job, reads like a note from me to a future me, and is small enough to read inside a single request.

The top-level index is the concierge. One line per entry, `[Title](file.md) — one-sentence hook`. Every session opens it first. If nothing there is relevant, the session proceeds on its own attention; if something is, it opens that one file and reads only what matters. The index does not hold the memories. It holds the map.

The whole layer is deliberately old-fashioned — filesystem, plain text, greppable. It is not fancy and does not need to be. It needs to survive session death and be readable by the next session. It does both.

## Layer two — the brain

The second layer is the brain server, and it exists because the first layer is only as portable as the machine it sits on.

The bundle solved session death. It did not solve me. I work across a desktop and a laptop, and the sessions that mattered were not always on the machine holding the files. I already had a VPS running the trading system around the clock, so the durable box was sitting there either way. Putting shared memory on it was less a design decision than noticing the obvious.

On that VPS I run a lightweight service holding a durable, queryable record of decisions, lessons, and state across every project I work on — not just the one on the laptop in front of me — exposed over MCP. Any Claude session, anywhere, can call `brain_digest()` for what has happened lately across the whole ecosystem, or `brain_context("trident-forge")` for what is current on one system.

That is what turns the local bundle from a per-machine artifact into a real substrate. On the laptop the local bundle is thin, but the brain is the same, and the session reconstructs its bearings from the shared source. When a session ends and the transcript is gone, what it decided outlives it.

The brain has its own failure modes — I run a reconciliation script for a known token-drift edge — but it is built fail-soft on purpose. If the brain is unreachable, sessions proceed on the local bundle and log a warning. Nothing blocks.

## Layer three — the discipline

The third layer keeps the first two useful, and it is the one people underestimate.

Files and a server do not create memory. What creates memory is writing things down at the moment they happen, in the format that will be consultable later, at a cadence that keeps up with the work. I learned that the way you learn most things — by having files that were technically present and quietly wrong.

Four rules govern the cadence. Every one of them is scar tissue:

1. **The moment a session corrects a class of behavior, a feedback memory gets written.** Not later. If I have to correct the same thing twice, the second correction is a bug in my memory bundle, not a bug in the model. That reframing is what turned correcting the AI from a chore into maintenance on a system I own.
2. **The moment a project decision locks, the project file gets updated** — decision, date, current-truth prose. Otherwise the next session picks up a plan I have already abandoned and executes it faithfully.
3. **The moment a paper, a repo, or a piece of finished work earns a second look, it gets saved in the same session.** I finished a substantial essay once and wrote no memory for it. Six days of sessions had no idea it existed, and I had to re-explain a finished thing to my own system. A reference I mean to save "next time" is a reference I have already lost.
4. **Every five to ten substantive exchanges, the session checkpoints anything worth surviving.** Added the day I lost about four hours to a session that dropped context without warning.

Without the discipline, files exist but they lie. With it, files are current-truth, and the substrate carries real weight.

## What this substrate has done for the work

Once memory lives outside every individual session, every downstream decision gets cheaper.

**Model routing gets cheaper.** A lighter, faster model can take a targeted task without re-learning who I am, because who I am is a file it can open. When live-money code needs the strongest model, I route deliberately — and that routing rule lives in the bundle too.

**Long projects get cheaper.** A week away no longer forces a re-briefing. My audio-plugin project, my ebook reader, my visual-effects rig for DJing, and my trading engine all sit in the substrate at once, each callable without polluting the others.

**Long conversations get cheaper.** When a session nears its context ceiling, the handoff-at-30-percent rule fires, it writes a handoff file, and the next session picks up the thread.

**The writing you are reading got cheaper.** I did not have to remember how I wanted this to sound. A `user_writing_voice.md` file gave the drafting session the register to reach for — written once, from a calibration I only had to do once.

**And most importantly, it compounds.** Every deep read lands as a reference or a note before the session ends. Every rule I lock lands as feedback. What I have learned over the past year is not scattered across dead transcripts — it is consolidated, cross-linked, and queryable.

## The maintenance costs

Nothing this useful is free. Three costs I pay to keep it healthy.

**Pruning against rot.** A rule that was correct in April can be wrong in July. If old memories are not corrected or retired, future sessions follow them dutifully and produce work that is confidently obsolete. A weekly pass is how I fight it.

**Compacting the index.** The system relies on the index being small enough to read in one shot. Past a certain size — I hit that ceiling again this week — the tail entries silently fall out of the read window.

**Reconciling contradictions.** A feedback rule and a project decision can quietly disagree. The verify-gate catches some before it reaches code; the weekly pass catches more. Neither catches everything. A graph-resolver would be ideal and someday will exist.

The substrate does not stop working when these accrue; it works less well until they are paid. Gardening, not firefighting.

## Why the architecture holds

The best proof I have is unremarkable, which is the point. I ran a machine-health diagnostic one week, wrote down what I found, and did nothing about it. A week later a different session on the far side of that gap opened the file, knew exactly what state the machine had been left in, and picked the work up mid-thought. Nothing heroic happened. Something simply did not have to be re-explained.

The three layers are what make that unremarkable. The local bundle keeps per-machine detail close and greppable. The brain keeps cross-machine truth durable and portable. The discipline keeps both current. Take one away and the whole thing degrades.

If you are building alone with AI over anything longer than a single sitting, the answer to *"how do I keep this coherent"* is not a bigger model, a longer context window, or a smarter chat UI. It is a memory system that lives outside any individual session, that you own end-to-end, and that you write to on a discipline. It does not have to be Markdown. It does not have to be a VPS. It does have to survive session death and be read by the next session, not just written for you.

The rest of what I build sits on top of this.

More field notes to follow.

— *Thomas Adair. Marine. DJ/Producer. Systems Architect — shipping across trading systems, music production, agentic tooling, and consumer apps with AI orchestration.*
