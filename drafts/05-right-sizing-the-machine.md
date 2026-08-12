---
title: "Right-Sizing the Machine: The Discipline and the Measure"
slug: "right-sizing-the-machine"
excerpt: "My always-on instruction context was 13,891 tokens a turn. I cut it 62.8% — and found the layer had drifted off its own purpose while I wasn't weighing it."
tags:
  - AI
  - solo-builder
  - field-notes
  - systems-architecture
  - context-engineering
feature: false
ready: true
---

**By Thomas Adair.** Marine. DJ/Producer. Systems Architect — shipping across trading systems, music production, agentic tooling, and consumer apps with AI orchestration.

*The model improves on its own. The machine you build around it is the part you own — which means it's the part you maintain.*

---

August of 2025. A friend got me into day trading, and around the same time I found out people were writing real software with AI.

I had never built a program in my life.

Those two things collided, and out of them came one specific idea: write a strategy in Pine Script, wire it through TradersPost into a prop firm account, and let it trade while I sleep. Not *I could make money* — I could build a thing, and the thing would work without me standing over it. That's the lightbulb, and everything since has been downstream of it.

What I've built in the year since is a live-money trading system and the entire AI substrate around it.

The substrate grew in layers, and every layer arrived because something broke first. For months the whole workflow was: open a chat, explain everything from the beginning, get some code, close the chat, lose it all, start over tomorrow. Then the tooling churned under me — OpenClaw, then PicoClaw, then Hermes, inside a single year, each one the obvious choice at the time, each switch costing me everything the last one held.

That's what forced the memory bundle. Files I own, on hardware I control, read by every session that opens. That was the last field note, and it's the substrate the rest of this sits on.

None of that is a straight line. It's a year of building the thing, watching a piece of it fail under real load, and replacing that piece with something that holds.

Underneath all of it, growing the whole time, was the operating context. I'd weighed that layer before — more than once. What I'd never done was weigh it on a schedule.

## The layer underneath

Not the memory. The operating context.

The instruction file the model reads before it reads anything else. The rule files stacked next to it. The skills. The whole standing brief every session receives before it does a single piece of work for me.

That layer grew the way the rest of it grew — a rule at a time, each one added the day something went sideways and I decided it shouldn't go sideways twice. Which is the correct way to build it. Every line in there was earned.

The problem isn't how it grew. The problem is that a set of rules only ever gets added to — and I'd been checking it occasionally, when something prompted me, instead of on a cadence that kept pace with how fast everything around it was moving.

And here's what I like about this layer: it's the same shape as the memory bundle, one level up. The bundle is progressive disclosure for my FACTS — an index always resident, the bodies pulled in only when something matters. This is progressive disclosure for the operating context itself. I'd already built the pattern. I just hadn't noticed it applied here too.

## Why I was looking

I audit this system on purpose. Not on a crisis — on a cadence.

That's the actual driver, and I want it stated plainly before I get to the research, because people will assume the research was the reason. It isn't. Hardening this rig as I go is how I work: I find the weak joint, I name it, I fix it, and I say out loud what I changed. Iterating in the open is the discipline, not an admission.

Building those self-checks in is deliberate. The project registry exists for exactly that reason — a standing inventory of what I'm running and where it stands, added specifically to keep me honest about a portfolio that got too wide to hold in my head. That's the pattern: when I notice I can't personally track something anymore, I build the thing that tracks it.

So the auditing habit was never the gap. The gap was narrower and more specific — I had never put the HARNESS itself on that footing. Its weight, its health, whether the rules in it still pointed at anything real … I checked those when something prompted me to. Occasionally. Never on a clock.

Every rule in that file got there the same way — something failed once, I decided it wouldn't fail twice, I wrote it down. That's a good instinct and it built a good system. It also has exactly one direction of travel. A rule set that only ever grows will keep working right up until the moment its own weight becomes the problem, and it will never tell you when you crossed that line. Nothing errors. Nothing warns you. It just costs more every turn than it returns.

And here's what makes the frequency the whole point rather than a detail. My output fluctuates — some weeks I ship constantly, some weeks I don't. The projects themselves change shape fast: a repo gets decommissioned, a tool gets swapped, a P0 moves. Every one of those events lands a little drift in the layer that every session reads. An occasional check can't keep up with that. The faster the operation moves, the more often its scaffolding needs weighing … and I'd had that exactly backwards, treating velocity as the reason I didn't have time for the pass.

Velocity is the reason the pass has to be on a clock.

I'd taken a pass at this exact layer the week before. It didn't fully hold — and I know that with certainty, because when I went back in this time the audit surfaced a lean-CLAUDE draft I'd started months earlier and never finished. I'd been circling this for a while, with good instincts and no leverage.

What I was missing was a mechanism. A reason to believe a cut was safe, and a rule for deciding what goes where.

That's what the reading gave me. Anthropic put out a post on the new rules of context engineering for Claude 5 [1], and the claim that stopped me was that they cut something like 80% of Claude Code's own system prompt and that the newer models came out BETTER — not worse. Alongside it, the Prompt-Induced Waste paper [2], which prices what over-stuffed and conflicting instructions actually cost you: roughly 15× the reasoning tokens on certain prompt padding, with no accuracy gain to show for it.

So: the discipline is why I was in there. The research is what made this pass stick.

Those aren't the same thing, and collapsing them gets the story backwards.

## Count first

Before any argument about what's worth keeping — weigh it.

**1,028 lines. Roughly 13,891 tokens, injected on every single turn.** A 330-line CLAUDE.md at about 4,962 tokens, plus all fifteen `rules/*.md` files at about 8,929.

Not fifteen files that *could* load. Fifteen that DO.

The mechanism is worth pinning down, because it's the part most people have wrong about their own setup. There's no `@import` line doing it. There's no hook. Claude Code loads memory files natively — the harness walks `~/.claude/`, concatenates what it finds as global memory, and hands the whole thing to the session before the first turn. Unconditionally. Whether the task needs a word of it or not.

That's a good mechanism. It's the same one that makes my memory index work — the index is resident because the harness puts it there, not because I remembered to ask for it.

But a mechanism that loads your index for free loads everything else for free too. It doesn't have taste. It has a directory.

Here's the part I'd underline. I had strong instincts about this layer for weeks and got nowhere. The number is what moved it. A well-tended instruction set is a year of hard-won corrections, and trimming it *feels* like handing back control you paid for — every builder knows that flinch. Instinct keeps a system heavy. The measurement is the only thing that frees it.

You can't right-size what you won't weigh — and you can't keep it right-sized by weighing it once.

## What a year of moving fast leaves behind

Then I read the thing. Line by line, the way you'd read a stranger's config.

There's no tool for this, which is worth knowing before you try. `/doctor` won't help — it's an auto-updater health check, no machine-readable output, nothing about what you're actually loading. So the pass is manual. You open every file, you count it, and you ask what it's still doing there.

Four things had drifted, and every one was billing me on every turn.

**A 65-line policy governing a tool that wasn't installed.** It commanded exclusive use of a particular MCP server and forbade my agent from using Read, Grep, and Bash — its own basic tools. Zero references to that server anywhere in my actual config. The audit had to violate the rule in order to run the audit … which is its own kind of answer.

**Five hooks firing every turn into that same missing tool.** Failing quietly.

I have a standing rule that an alarm must never be silenceable by the same failure it reports — that "non-fatal" is a claim you justify, not a claim you assume. Five hooks failing into a void is precisely the class of thing that rule exists to surface, and surfacing it is what the audit is FOR. It's also why that rule is one of the two I kept resident. More on that below.

**A 39-line integration calling functions that don't exist.** Marked *use every session*, calling my brain service by names I'd since renamed and never propagated.

**A stale project index** — a decommissioned repo still listed as my live P0, the system that actually holds that slot missing entirely, dead paths scattered through it.

This is what entropy looks like in a system built hard and fast by one person, under real time pressure, across a year of shipping. The tool gets renamed and the doc doesn't. The MCP comes out and its 65-line policy stays behind like a fossil. Hand-maintained indexes drift, always, everywhere, because that's what hand-maintained means.

Every serious rig accumulates this. The difference isn't whether it happens.

The difference is whether you go looking … and I found all four in one pass, because I did.

## The inversion

The finding that reorganized the whole project came next.

My real rules — the ones a model genuinely cannot guess — weren't in the file at all.

The ADHD five-item output cap. No-yes-man. Plain-language alerts. No LLM in the hot path. Exits are sacred. The TradersPost exit-payload spec that governs live money leaving a position.

None of it in CLAUDE.md. None of it in `rules/`. It lived in a plugin and in scattered session transcripts — which is to say, it lived nowhere that loads.

Sit with the shape of that. I was paying 13,891 tokens a turn for procedure a current model derives on its own, while the handful of things it genuinely needs FROM ME — my taste, my output shape, the hard safety rails around live money — weren't written down in any file it would ever read.

That's not a bloat problem. That's a layer that had drifted off its own purpose.

## Two jobs, not one

It also broke the frame I'd been stuck in, which was *keep it all* versus *cut it down.* Both answers are wrong, because that context is doing two entirely different jobs and I'd never separated them.

There's **who I am and what must never happen** — always true, always resident.

And there's **procedure** — situational, real, worth keeping, and dead weight on every turn that doesn't need it.

Anthropic's post [1] hands you the sorting test in a single line: *could the model figure this out on its own? If yes, cut it.*

Applied honestly, the test took out most of the weight on contact. And my actual rules passed it — which means the restructure's first job was to write them in for the first time.

The audit ADDED, even as it cut. I didn't expect that going in, and it's the most useful thing I took out of the pass.

## Where the procedure went

The mechanism is unglamorous, which is usually the sign it's right: **skills, triggered by their descriptions.**

The always-on layer collapses to a thin table of contents. Identity. The hard rails. One line per skill. The memory index. That's the resident set.

The bodies live in skill files and load when the task matches the description — which makes the description the lever. The entire system's precision now lives in one line of text per skill. A vague description is a skill that never fires, or one that fires on everything.

Seven procedural rules moved that way: the loop-engineering verification ladder, the orchestration playbooks, model-routing, npm lockdown, agent mental models, skill authoring, fleet orchestration. Six more were generic guardrails a current model handles unassisted — archived.

Index resident, bodies on demand. Same shape as the memory bundle. One layer up.

## What it came to

**13,891 tokens down to 5,167 always-on. A 62.8% cut — about 8,700 tokens handed back every turn.**

Across a fifty-turn working session, that's north of four hundred thousand tokens no longer spent re-reading things the model didn't need.

One note on that number, because I'd rather report the one I hit than the one I aimed at: the plan I wrote going in projected a 92% cut. The gap is the two rails I chose to keep and the real rules I had to write in. I'll take the trade.

And none of it came from throwing away the discipline. It came from RELOCATING it — and from finally writing down the rules that mattered most. Lighter and more correct, which is not the tradeoff I expected to be offered.

The stale index got the same treatment one level down. It regenerates on a schedule now instead of being hand-carried. Same move as everything else here: stop maintaining state by hand when it can load itself fresh.

## What I kept, and why

Don't over-trim. The test cuts both ways, and the failure mode on the far side is worse than weight.

Two rules stayed resident, and both are trading-safety rails: async loop safety, and fail-loud observability. Both came out of the same P0 — a live system that dropped exit signals silently for hours because an async client was cached across event loops and the alarm that should have screamed was riding the exact path it was meant to be watching.

Every instinct in this piece says move those to skills. I kept them, and the reasoning is the whole caution:

**A skill fires on a trigger. These failures don't have one.**

They're silent by construction. No session ever announces *we are now writing async code that caches a loop-bound client across an `asyncio.run()` boundary* — that's the entire nature of the bug. It arrives disguised as ordinary working code. By the time any trigger could fire, the landmine is already in the file.

Load-on-demand is right for procedure you'll know you need. It's wrong for a failure mode whose defining property is that you don't see it coming.

So the sorting comes out like this. Derivable procedure goes. Non-derivable taste stays. Silent, non-triggerable, expensive-to-discover failure modes stay resident even when the token math argues otherwise — because the token math isn't pricing the outage.

Right-sizing isn't minimizing. It's putting each thing where it belongs: the always-true resident, the situational one reach away, the derivable gone.

## Landing

The model is the part that improves on its own. Every quarter, without me, whether I maintain a single thing or not.

The machine around it is the part I own. Which makes it the part that drifts — quietly, always toward more, always in the direction I'm not looking.

That's not a flaw in how I built it. That's what a system does while you're busy shipping.

So I weigh it, on a cadence, and I move what's in the wrong place.

Right-size it, or pay the tax on every turn you take.

---

## References

[1] Thariq Shihipar (Anthropic). "The new rules of context engineering for Claude 5 generation models." *Claude by Anthropic*, July 2026. https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models — Source for the ~80% system-prompt reduction and the "could the model figure this out on its own?" sorting test.

[2] *Prompt-Induced Waste.* arXiv:2608.01347. — Source for the ~15× reasoning-token cost of prompt padding with no accuracy gain.

---

— *Thomas Adair. Marine. DJ/Producer. Systems Architect — shipping across trading systems, music production, agentic tooling, and consumer apps with AI orchestration.*
