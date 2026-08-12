---
title: "Right-Sizing the Machine: The Discipline and the Measure"
slug: "right-sizing-the-machine"
excerpt: "My always-on instruction context was 13,891 tokens a turn. I cut it 62.8% — and the audit found it wasn't just heavy, it was pointed at the wrong things."
tags:
  - AI
  - solo-builder
  - field-notes
  - systems-architecture
  - context-engineering
feature: false
ready: false
---

**By Thomas Adair.** Marine. DJ/Producer. Systems Architect — shipping across trading systems, music production, agentic tooling, and consumer apps with AI orchestration.

*The model keeps getting better on its own. The machine you build around it does the opposite — quietly, and only where you aren't looking.*

---

The last field note was about giving my AI a memory that survives the session. A folder of Markdown, an index at the top, the bodies pulled in only when something in the index actually matters. Progressive disclosure for my *facts*.

This one is the same instinct, one layer up.

Not the facts — the operating context. The instruction file the model reads before it reads anything else. The rule files sitting next to it. The skills. The whole standing brief I hand every session before it has done a single piece of work for me.

That layer had quietly become the problem. And it took me a while to see it, because it was the part I was most proud of.

## The two things this piece is actually about

There's a discipline and there's a measure, and neither one writes this article alone.

The **discipline** is that auditing my own system is a standing practice. I didn't stumble into this. I'd taken a pass at this exact problem the week before and it hadn't fully stuck — I know that for certain, because when I went digging this time the audit surfaced an abandoned lean-CLAUDE draft I'd started and never finished. I'd been circling this thing for a while.

The **measure** is what finally made it hold. Because the discipline gets you to look, and then your gut talks you out of it. Every builder knows the feeling: a well-tended instruction set is a year of hard-won corrections, and trimming it feels like handing back control you paid for. The count is what overrides the flinch. Instinct keeps a system bloated. The number is the only thing that frees it.

Everything below is anchored to something I measured. Where it isn't, I'll say so.

## The catalyst

Three things converged.

The standing habit was already running. The half-finished pass from the week before was already sitting there, unresolved. What was missing was a mechanism — a reason to believe the cut was safe, and a rule for deciding what went where.

That came from the reading. Anthropic put out a post on the new rules of context engineering for Claude 5, and the claim in it that stopped me was that they cut something like 80% of Claude Code's own system prompt and the newer models came out *better*, not worse. Alongside it, the Prompt-Induced Waste paper (arXiv 2608.01347) — which puts numbers on what over-stuffed and conflicting instructions actually cost you. Measured at roughly 15× the reasoning tokens on certain prompt padding, with no accuracy gain to show for it.

That's the part that reframed it for me. I'd been treating my instruction file as insurance. It reads better as a bill.

## So I stopped arguing with myself and counted

Before any philosophy: weigh the thing.

**1,028 lines. Roughly 13,891 tokens, injected on every single turn.** A 330-line CLAUDE.md at about 4,962 tokens, plus all fifteen `rules/*.md` files at about 8,929.

Not fifteen files that *could* load. Fifteen that *do*.

That mechanism is worth being precise about, because it's the part most people get wrong about their own setup. There's no `@import` line doing it. There's no hook. Claude Code loads memory files natively — the harness walks `~/.claude/`, concatenates what it finds as global memory, and hands the whole thing to the session before the first turn. Unconditionally. Whether the task needs a word of it or not.

I want to be clear that this is a good mechanism. It's the same one that makes my memory index work — the index is always resident because the harness puts it there, not because I remembered to ask. But a mechanism that loads your index for free will load your cruft for free too. It doesn't have taste. It has a directory.

So: a tax, on every message, forever, in exchange for a set of instructions I had never once weighed.

You can't right-size what you won't weigh.

## Then I actually read it

This is the part only I can tell, and it's the part I'd have preferred not to find.

It wasn't just heavy. It was **wrong** in four specific places, and every one of them was costing me on every turn.

**A 65-line policy governing a tool that wasn't installed.** It commanded exclusive use of a particular MCP server and *forbade* my agent from using Read, Grep, and Bash — its own basic tools. Zero references to that server anywhere in my actual config. It was never installed, or it had been removed and the policy hadn't. The audit had to violate the rule in order to run the audit.

**Five hooks firing every turn into that same missing tool.** Failing silently. Every session, all year.

That one is a personal indictment, and I'll take it. I have a standing rule — it's one of the two I ended up *keeping* — that says an alarm must never be silenceable by the same failure it reports, and that "non-fatal" is a claim you have to justify. Five hooks failing quietly into a void is exactly the thing that rule exists to prevent. I wrote the rule. I still shipped the landmine. Rules you don't audit are decorations.

**An integration calling functions that don't exist.** Thirty-nine lines, marked *use every session*, instructing the model to call my brain service by names I'd apparently renamed at some point and never propagated. The section pointed at dead names. It would have failed on every call it ever made.

**A stale project index** — listing a decommissioned repo as my live P0, omitting the system that actually is, with dead paths scattered through it.

Here's the honest framing, and I've thought about how to say it. This is not what a sloppy setup looks like. This is what *entropy* looks like in a system built hard and fast by one person, under real time pressure, across a year of shipping. Every serious, lived-in rig grows this. The tool gets renamed and the doc doesn't. The MCP gets removed and its 65-line policy stays behind like a fossil. The index drifts because hand-maintained indexes always drift.

What almost nobody does is *measure it and fix it*. That's the part I'd put my name on. Not "I kept it tidy" — I didn't. The discipline is the audit.

## The inversion

And then the finding that actually stung.

My real rules — the ones a model genuinely cannot guess — **weren't in the file at all.**

The ADHD five-item output cap. No-yes-man. Plain-language alerts. No LLM in the hot path. Exits are sacred. The TradersPost exit-payload spec that governs live money moving out of a position.

None of it was in CLAUDE.md. None of it was in `rules/`. It lived in a plugin and in scattered session transcripts — which is to say, it lived nowhere that loads.

So I was paying 13,891 tokens a turn for procedure the model can now derive on its own, while the handful of things it genuinely needs *from me* — my taste, my output shape, my hard safety rails around live money — weren't written down anywhere it would ever read them.

That's not a bloat problem. That's a system pointed at the wrong things.

It also broke the impasse, because it killed the frame I'd been stuck in. I'd been arguing with myself about *keep it all* versus *gut it*, and both answers were wrong, because my context was doing two entirely different jobs and I'd never separated them.

There's **who I am and what must never happen** — always true, load it always. And there's **procedure** — situational, real, worth keeping, and dead weight on every turn that doesn't need it.

Anthropic's post gives you the sorting test in one line: *could the model figure this out on its own? If yes, cut it.*

Applied honestly, most of my bloat failed that test immediately. And my actual rules passed it — which meant the restructure's first job was to **write them in for the first time.**

The audit added, even as it cut. I didn't expect that going in.

## Where the procedure went

The mechanism is unglamorous, which is usually a good sign: **skills, triggered by their descriptions.**

The always-on layer collapses down to a thin table of contents. Identity. The hard rails. A one-line description per skill. The memory index. That's the resident set.

The bodies live in skill files and load when the task matches the description. Which makes **the description the lever** — the entire system's precision lives in one line of text per skill, and a vague description is a skill that never fires or fires on everything.

Seven procedural rules moved that way: the loop-engineering verification ladder, the orchestration playbooks, model-routing, npm lockdown, agent mental models, skill authoring, fleet orchestration. Six more were generic guardrails a frontier model now handles unassisted — those got archived outright.

And note the rhyme, because it's the reason this piece is a sequel and not a fresh idea: the memory bundle already does exactly this for facts. Index always resident, files on demand. Same shape, one layer up. I'd already built the pattern and hadn't noticed it applied here.

## What it came to

**13,891 tokens down to 5,167 always-on. A 62.8% cut — about 8,700 tokens handed back every turn.**

Across a fifty-turn working session that's north of four hundred thousand tokens I'm no longer spending to re-read things the model didn't need.

I want to be precise about what that number is and isn't, because the plan I wrote going in projected a 92% cut, and 62.8% is what the execution actually produced. The gap is the two rails I decided to keep and the real rules I had to write in. I'd rather report the number I hit than the number I aimed at.

And it didn't come from throwing away my discipline. It came from **relocating** it — and from finally writing down the rules that mattered most. The machine came out lighter *and* more correct, which is not the tradeoff I expected to be offered.

The stale index got the same treatment, one level down: it regenerates on a schedule now instead of being hand-maintained. Same move as everything else here. Stop hand-carrying state that can load itself fresh.

## The honest caution

Don't over-trim. The test cuts both ways, and the failure mode on the other side is worse than bloat.

Two rules stayed always-on, and both are trading-safety rails: async loop safety, and fail-loud observability. Both were born from the same P0 — a live system that dropped exit signals silently for hours because an async client was cached across event loops, and the alarm that should have screamed rode the exact same broken path it was meant to be watching.

Every instinct in this article says move them to skills. I kept them anyway, and the reasoning is the whole caution:

**A skill fires on a trigger. These failures don't have one.**

They're silent by construction. There is no moment where the session announces "we are now writing async code that will cache a loop-bound client across an `asyncio.run()` boundary" — that's precisely the class of bug that arrives disguised as ordinary working code. By the time a trigger could fire, the landmine is already in the file. Load-on-demand is a fine strategy for procedure you'll know you need. It's a terrible strategy for a failure mode whose defining property is that you don't see it coming.

So: derivable procedure goes. Non-derivable taste stays. Silent, non-triggerable, expensive-to-discover failure modes stay, and they stay resident even when the token math says otherwise, because the token math isn't pricing the outage.

Right-sizing isn't minimizing. It's putting each thing where it belongs — the always-true stuff resident, the situational stuff one reach away, the derivable stuff gone.

## What I'd tell you to do first

Count. Before anything else, before any opinion about what's worth keeping, weigh what you're actually loading on every turn.

I'd been circling this problem for weeks with good instincts and a standing habit of looking, and I got nowhere until I had a number. The number is what made the cut safe to make — not braver, *safe*, because once you can see the bill you're no longer trading against a feeling.

Then read it. Not skim it. Read your own instruction file line by line like it belongs to a stranger who might be lying to you. Mine was pointed at an uninstalled tool, calling dead function names, firing five hooks into nothing, and missing every rule I'd actually have fought for.

That's not the read I expected. It's the read I'd bet most people get.

## Landing

The model is the part that improves on its own. Every quarter, without me, whether I maintain anything or not.

The machine around it is the part I own. Which means it's also the part that rots — quietly, in the direction of more, always where I'm not looking.

Right-size it, or pay the tax on every turn you take.

---

*These field notes feed the monthly Trident Digest — the short-form version of what I'm learning, once a month, for people building alone with AI. Subscribe below, or find me on Threads.*

— *Thomas Adair. Marine. DJ/Producer. Systems Architect — shipping across trading systems, music production, agentic tooling, and consumer apps with AI orchestration.*

---

## Draft notes — [AUTHOR] gaps and grounding

**[AUTHOR] markers in this draft:** none inline. Everything asserted is grounded in the audit plan, the outline, or the verified restructure figures. Two items below need your eyes before this goes live, but I did not want to break the prose with markers for them — flagging here instead.

1. **The Anthropic "~80% of Claude Code's system prompt" figure.** This comes from your own outline (Beat 2), not from my reading of the post. I carried it forward as written but did not independently verify it. Confirm the number and the framing before publish. Also needs the exact post title + URL for a proper citation — I referenced it descriptively as "the new rules of context engineering for Claude 5."

2. **The seven skills named in "Where the procedure went."** Your brief said 7 procedure rules moved to skills but did not enumerate them. I named them from the skills table in your current CLAUDE.md (loop-engineering, workflow/fleet orchestration, model-routing, npm-security, agent-mental-models, skill-authoring). Verify the list matches what actually moved — the count is right, the specific names are my inference from the current always-on table.

**Outline sections I deliberately did not ground:**

- **The 92% / 14k→1.15k payoff figure** (outline Beat 7, and the restructure plan's "Net effect"). That was the *projection*, not the result. I used your verified 13,891 → 5,167 / 62.8% throughout and added one honest sentence naming the gap between plan and outcome. If you'd rather not surface the plan-vs-actual delta at all, cut the paragraph beginning "I want to be precise about what that number is."
- **Outline Beat 7's "~635k across a working session."** That was derived from the 12,740 projection. I recomputed from the real 8,724 figure and stated the 50-turn assumption inline rather than presenting it as measured.
- **Outline Beat 4's callback** — "the memory-bundle index outgrew its read-cap mid-restructure." Listed as an optional anecdote. I left it out; the piece already carries its sequel weight and this would be a third callback to Article 1. Easy to add back if you want it.
- **Open question 1** (how much of the real CLAUDE.md to show). I showed no verbatim config and named the broken pieces functionally — "a particular MCP server," "my brain service" — rather than by product name. Your outline's open question 2 flagged this as your call. Naming them is more vivid; say the word and I'll name them.
- **Open question 3** (subtitle). Kept the locked "The Discipline and the Measure" as the subtitle and folded it into the frontmatter title. The alternate punchy subtitle from the outline is built on the 92% number, so it's stale regardless.
