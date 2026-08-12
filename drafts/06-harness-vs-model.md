---
title: "Harness vs. Model: Why I Built My Own"
slug: "harness-vs-model"
excerpt: "The thing that keeps failing isn't the model. It's the scaffolding around it — the prompts, the tools, the memory, the orchestration. That part you can own."
tags:
  - AI
  - solo-builder
  - field-notes
  - systems-architecture
  - AI-orchestrated-development
feature: false
ready: false
---

**By Thomas Adair.** Marine. DJ/Producer. Systems Architect — shipping across trading systems, music production, agentic tooling, and consumer apps with AI orchestration.

*Field notes on the part of the system nobody upgrades.*

---

An agent botches a task and the reflex arrives before the thought does: *the model isn't smart enough.*

So you switch. Pay for the bigger one. Wait for next month's release, because there's always a next month's release and it's always better than this month's.

I did that for the better part of a year. It rarely fixed anything.

What it took me too long to notice is that my failures had a *shape*, and the shape didn't move when the model did. The same work got re-explained. The same corrections got given twice. The same context evaporated at the same seams. A stronger model did that work faster and more fluently, and then lost it in exactly the same place, for exactly the same reason.

That's not a model problem. That's a problem with everything *around* the model.

## Naming the thing around the model

There's a word for it and it isn't a great one, but here it is: the **harness**.

Everything that isn't the model. The system prompt it wakes up inside. The tool definitions re-sent on every single turn. The memory it can read, if it can read any. The way work gets broken up, dispatched, approved, verified. The rules that load whether they're relevant or not.

The model is the engine. The harness is the whole car — the transmission, the fuel line, the dashboard, the fact that the steering wheel is connected to anything.

Most people rent the entire car and spend all their time complaining about the engine.

## I'd been paying this bill before it was priced

I want to be careful about the order of events here, because the tempting version of this story is *I was right and then the research proved it*, and that's not what happened. What happened is that I lost to the same failure enough times to build around it, and then, months later, two papers turned up and put numbers on the bill I'd already been paying.

The first is **Prompt-Induced Waste** (arXiv 2608.01347). The finding that reorganized my thinking: an identical model, running an identical task, with an identical prompt, can cost **5–30× more** depending on nothing but the harness it's running inside. Same engine. Same trip. Thirty times the fuel.

It gets more specific, and more uncomfortable. A common harness re-transmits a fixed prefix of **16,000–20,000 tokens on every turn** — tool schemas, instruction blocks, inventories you never see and can't touch. Padding a prompt with "develop and compare several approaches" burns roughly **15× the reasoning tokens** with no accuracy gain to show for it. Generic "think deeply" phrasing runs **1.6–2.2×**, same result: more spend, same answer. And a *misleading architectural hint* — one wrong steer in the framing — costs **2.61×**, because the model dutifully chases the thing you accidentally pointed it at.

Read that list again and notice what's on it. Not one of those is a model deficiency. Every one is a decision someone made about the scaffolding, and in most setups that someone isn't you.

The second is **Model or Harness?** (arXiv 2607.28802), and its contribution is a taxonomy — which sounds academic until you try to debug an agent without one. It splits agent failures into fault families, and the harness gets its own: context, memory, tools, subagents. Separate from the model. Its own diagnosis, its own fix.

That distinction is the whole practical payoff, and I've since folded it into how I work: label the fault side *before* touching code. Was that a model failure, a harness failure, a tool failure, a memory failure, an eval failure? Because the fixes don't transfer. A harness failure — a contract dropped in a handoff between two agents — will not be fixed by a smarter model or a better prompt, and you can burn a whole afternoon proving that to yourself. Patching the wrong side is the most common wasted fix I make.

The paper also names seven distinct ways *memory* fails — stale state, pollution, redundancy, overgeneralization, a decision never written down, a decision written down and never retrieved, and the rationale getting stripped out until a rule survives with no *why* attached and no way to falsify it.

I'd met most of those personally. I just hadn't known they had names, or that they were one family.

## What a bad harness actually costs, from my seat

Make it concrete, because the numbers above are someone else's measurements and mine are the ones I can vouch for.

**The prefix you don't control.** In my own setup — mine, the one I built — I was loading 13,891 tokens of instruction on every turn before the session did a single useful thing. I only know that because I finally measured it. In a harness that isn't yours, you don't get to measure it. You just pay it.

**The tools you can't trim.** A subagent whose only job is to read three files does not need the full inventory of every tool in the system re-described to it. Trimming schemas per role is a real lever with a real payoff — and it exists only if you own the layer where schemas are assembled.

**The memory that evaporates when the vendor changes it.** OpenClaw, then MoltBot, then Hermes — inside one year. Every one of them was the obvious choice at the time. Every switch cost me everything the last one held. That's the sentence the memory-bundle piece grew out of, and it's a harness story from beginning to end. The model was never the thing I lost.

**The tax on prompts nobody audits.** Fifteen times the reasoning tokens for a phrase that sounds like diligence. If your harness templates that phrasing into every dispatched task — and plenty do — you are paying it on every task, and there is no setting for it.

Every one of those is a line item. In a rented harness, every one of them is also a line item you cannot reach.

## So I built my own

Not out of principle. Because those specific levers were the ones I needed my hands on.

What owning it actually buys, concretely:

**Bounded prompts.** Every child prompt I dispatch carries the same three things: explicit scope — which files are in play — a smallest-sufficient-change instruction, and a named stop condition. The banned phrasing is banned at the template level, which means the 15× tax gets paid zero times instead of every time. Effort comes from choosing the model tier, not from stacking adjectives on the prompt.

**Tool schemas trimmed per role.** The reader agent gets the reader's tools. Prefix hygiene is where the cost leaks actually live — not in how any single request is worded — and it's the first place I look now when a session feels expensive, before I blame the conversation.

**A memory that's mine to read and edit.** Plain Markdown. Greppable. Wrong facts get fixed by editing a sentence. Covered in full in the previous field note, and it is the single load-bearing piece of the whole thing.

**An audit trail I can actually see.** Which is what makes any of the above verifiable rather than aspirational.

And the piece before this one is the clearest case study I have: I cut my always-on operating context by 62.8% and simultaneously discovered it was pointed at an uninstalled tool, calling dead function names, and missing every rule I'd genuinely have fought for. Not one line of that was model work. All of it was harness work, and all of it was reachable only because the harness was mine.

## The trading proof

The argument stops being abstract when there's live money in it, and there are two examples I keep coming back to — one as a foil, one as something stranger and more convincing.

**The foil: a vendor-owned agentic trading environment.** Billed as the first of its kind — the whole scaffold delivered as a product. Convenient. Genuinely impressive in places. And entirely theirs: their orchestration, their memory model, their prompts, their upgrade schedule, and, as far as anyone outside can tell, an architecture that keeps AI inside the execution loop.

*[AUTHOR: needs the product name (OmniPhi per your outline), a source link, and — most importantly — verification of the "AI in the execution loop" claim. That's a specific architectural assertion about a real company. I won't assert it on outline-notes alone. If it can't be sourced, the beat still works with the claim cut down to "their scaffold, their lock-in."]*

**The convergence: a stranger's engine that arrived where I did.** A public Polymarket trading system, built by someone I've never spoken to, with no shared influences I'm aware of — and it lands on the exact doctrine I'd fought my way to. No LLM anywhere in the execution path. The agent builds and tunes the strategy offline, then gets out of the way. Deterministic risk gates. Breakers that survive a restart.

*[AUTHOR: needs the repo name/link (Polybot per your outline) and a check that the four architectural claims above match what's actually in it. Your outline flagged whether to name it directly as your call — I've described it unnamed pending that.]*

That second one is the more interesting evidence, and it's the reason this beat exists.

When two people, working alone, in different markets, without coordinating, land on the same harness discipline — that's not taste. Taste diverges. When independent solutions converge on the same shape, the shape is being dictated by the problem.

And the shape both of us landed on is a statement about the harness, not about the model: **the model does its work offline, and the thing that touches live money is deterministic and inspectable.** The intelligence goes in the design loop. It does not go in the execution loop.

## What it costs to own it

I'd rather say this plainly than let you find out at 1am.

Owning your harness means you maintain it. You debug it. There is no vendor to escalate to, no status page to check, no support thread where someone else is already on it. When it breaks at one in the morning it breaks in code you wrote, and the person qualified to fix it is you, and the reason it broke is probably also you.

The 62.8% cut in the last piece is the honest illustration. That entropy accumulated in a harness I *own*. Ownership didn't prevent the rot. It gave me somewhere to stand while I measured it.

Most people should not do this. If your work lives in one tool, on one machine, and mostly looks like conversation — the rented harness is better than what you'd build, and it's better on day one instead of month six. Building your own scaffolding out of principle when a product would do is a very elaborate way of not shipping.

Here's my line.

I own it because the failures that were actually killing me lived in the harness, and I'd rather be able to reach them.

That's the whole calculus. Not that owning it is virtuous — it isn't, it's a maintenance bill. It's that when the failure is in a layer you don't control, your only remaining move is to wait for someone else's next release and hope it happens to help.

## Landing

Come back to the original suspect.

The model is rented. It'll be a different one next quarter, and that's fine — that's the good part. It improves without me, on someone else's schedule, at someone else's expense. I don't want to own it.

The harness is the part that stays. It's the part that holds your memory, spends your tokens, shapes every prompt you send, and quietly decides how much of your work survives the session.

Build the part you keep.

---

*These field notes feed the monthly Trident Digest — the short-form version, once a month, for people building alone with AI. Subscribe below, or find me on Threads.*

— *Thomas Adair. Marine. DJ/Producer. Systems Architect — shipping across trading systems, music production, agentic tooling, and consumer apps with AI orchestration.*

---

## Draft notes — [AUTHOR] gaps and grounding

**Inline [AUTHOR] markers left in the draft — 2, both in "The trading proof":**

1. **The vendor foil (OmniPhi).** I would not assert "AI kept in the execution loop" about a named real company on the strength of an outline note. Needs the product name confirmed, a source link, and verification of that architectural claim. The beat is written so it survives if the claim gets cut — the lock-in argument stands on its own.
2. **The convergence case (Polybot).** Needs the repo link and a check of the four architectural claims (no LLM in execution path / offline tuning / deterministic risk gates / restart-proof breakers). Left unnamed pending your call from outline open question 3.

**Outline sections I couldn't ground, and what I did instead:**

- **Beat 5, Dispatch / Conductor internals.** Your outline names these as the harness you built; I have no source describing what they actually do. Rather than invent architecture, I wrote the beat around the four capabilities your outline lists — bounded prompts, per-role schema trimming, an owned memory bundle, an audit trail — all of which I *could* ground in the Agent Task Hygiene section of your CLAUDE.md. The systems are described by what they buy, not by name or internals. Your outline's open question 2 was exactly this tension (how much to reveal), so the conservative version seemed like the right default. Add the names and specifics if you want it more concrete.
- **Beat 1's "a specific botched run."** Your outline's voice note asks to open on one concrete failure, not theory. I don't have a specific incident I could report faithfully, so I opened on the *pattern* — failures with a shape that model upgrades didn't move — which is grounded in the re-explaining loop from Article 1. **This is the biggest remaining gap in the piece.** One real botched run, named, would meaningfully strengthen the open.
- **Beat 3's framing.** Kept your "here's the measured version of a bill I'd already been paying" order deliberately, including a sentence disclaiming the *I was right all along* reading.
- **Beat 6's bridge to Article 3.** The outline positions this beat as the setup for the adversarial-dynamical-systems piece. I gestured at it (intelligence in the design loop, not the execution loop) without an explicit "more on this next time," since 03 is already published — adjust if you want a direct back-reference to it instead.
- **Placement note.** Your outline sequences this after Article 2 and before Article 3. The brief for this pass framed it as the thesis behind the right-sizing piece, so I tied it forward to both the memory bundle and the right-sizing restructure. If it publishes in the original slot instead, the right-sizing references in "So I built my own" need to become forward-looking.
- **Title.** Kept the working title. Your outline's alternates — "Build the Part You Keep," "The Model Is Rented," "Own the Scaffolding" — are all live; note that "Build the part you keep" is currently the closing line, so promoting it to the title would mean re-landing the ending.

**Numbers used and where they came from:** 5–30× harness variance, 16–20k re-transmitted prefix, ~15× for "compare several approaches," 2.61× for a misleading hint — all from your Prompt-Waste outline notes (arXiv 2608.01347). The 1.6–2.2× "think deeply" figure and the fault-label taxonomy come from your CLAUDE.md Agent Task Hygiene block. 13,891 tokens and 62.8% are the verified figures from the right-sizing audit. No number in this draft is mine.
