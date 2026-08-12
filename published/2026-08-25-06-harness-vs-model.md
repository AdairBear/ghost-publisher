---
title: "Harness vs. Model: Why I Built My Own"
slug: "harness-vs-model"
excerpt: "The thing that kept failing was never the model. It was the scaffolding around it — the prompts, the tools, the memory, the dispatch. That part I can own."
tags:
  - AI
  - solo-builder
  - field-notes
  - systems-architecture
  - AI-orchestrated-development
feature: false
ready: true
---

**By Thomas Adair.** Marine. DJ/Producer. Systems Architect — shipping across trading systems, music production, agentic tooling, and consumer apps with AI orchestration.

*Field notes on the part of the system nobody upgrades.*

---

An agent botches a task and the reflex arrives before the thought does: *the model isn't smart enough.*

So you switch. Pay for the bigger one. Wait for next month's release — because there's always a next month's release, and it's always better than this month's.

I did that for the better part of a year. It rarely fixed anything.

My failures had a shape, and the shape never moved when the model did. The same work got re-explained. The same corrections got given twice. Context evaporated at the same seams every time. A stronger model did that work faster and more fluently … and then lost it in exactly the same place, for exactly the same reason.

That's not a model problem. That's everything AROUND the model.

## Naming it

There's a word for that everything, and it isn't a great one: the **harness**.

The system prompt the model wakes up inside. The tool definitions re-sent on every turn. The memory it can read, if it can read any. The way work gets scoped, dispatched, approved, verified. The rules that load whether they're relevant or not.

The model is the engine. The harness is the whole car.

Most people rent the car and spend all their time complaining about the engine.

## I'd been paying the bill before it was priced

I want the order of events straight, because the flattering version of this story is *I was right and then research proved it* — and that isn't what happened.

What happened is I lost to the same failure often enough to build around it. Months later, two papers turned up and priced the bill I'd already been paying.

**Prompt-Induced Waste** [1] found that an identical model, running an identical task, on an identical prompt, can cost 5–30× more depending on nothing but the harness it runs inside. Same engine, same trip, thirty times the fuel. It gets more specific: a common harness re-transmits 16,000–20,000 tokens of fixed prefix every turn — the standing block of instructions and tool definitions that goes out ahead of every message you send, relevant or not. Padding a prompt with *develop and compare several approaches* burns roughly 15× the reasoning tokens for no accuracy gain. Generic *think deeply* phrasing runs 1.6–2.2× — more spend, same answer. A misleading architectural hint costs 2.61×, because the model dutifully chases whatever you accidentally pointed it at.

Not one of those is a model deficiency. Every one is a decision somebody made about the scaffolding — and in most setups, that somebody isn't you.

**Model or Harness?** [2] contributes a fault taxonomy — a fixed vocabulary for the ways an agent run can fail. That sounds academic until you try debugging an agent without one. It splits agent failures into fault families and gives the harness its own: context, memory, tools, subagents. Separate from the model. Its own diagnosis. Its own fix.

That one distinction changed how I work. I now label the fault side before touching code — `planner—executor · fault:harness` when a contract gets dropped in a handoff, `agent—mcp · fault:tool` when a tool returns malformed JSON. The sides are model, harness, tool, memory, and eval — and the fixes don't transfer between them. A `fault:model` label routes to a prompt or tier change. A `fault:harness` label routes to a scaffold change. Patching the wrong side is the most common wasted fix I make, and the label is what stops me making it.

The same paper names seven distinct ways memory fails: stale state, pollution, redundancy, overgeneralization, a decision never written down, a decision written down and never retrieved, and rationale erosion — where the *why* gets stripped out and you're left with a standing rule nobody can falsify.

I'd met most of those personally. I hadn't known they were one family.

## What my own harness was costing me

The numbers above are someone else's measurements. Here are mine.

**The prefix I wasn't watching.** In my own setup — mine, the one I built — I was loading 13,891 tokens of instruction on every single turn before the session did a minute of useful work. That was the last field note: a 62.8% cut, down to 5,167 always-on. In a harness that isn't yours, you don't get to measure that. You just pay it.

**The tool surface I hand each agent.** Cost leaks live in that re-transmitted per-turn prefix — the tool schemas, the skill blurbs, the MCP inventories listing every external tool server the agent could theoretically reach for — not in how any single request is worded. A subagent whose only job is reading three files does not need the full MCP surface described to it. So schemas get trimmed per role, and when a session feels expensive I audit the prefix BEFORE I blame the conversation. That lever only exists if you own the layer where schemas get assembled.

**The memory that left with the tool.** OpenClaw, then PicoClaw, then Hermes — inside one year. Each the obvious choice at the time. Each switch cost me everything the last one held. The model was never the thing I lost.

## Bought on the promise

That last one deserves more than a line, because the churn wasn't restlessness. Each of those tools I picked up for a specific reason: it promised something my setup didn't have yet. Every one of them was a real answer to a real gap I'd hit that month.

Not one of them delivered on it completely.

That's the gap I want named, because it's the one nobody puts in the README. The promise is coherent. The demo holds. And then the thing you switched FOR is the thing that thins out around month three — it does eighty percent of what you came for; the last twenty is the part your work actually depends on, and the last twenty is the part you can't reach from the outside.

Hermes is the one that stuck, and I'll be straight about its status: it still hasn't fully delivered either. I'm still working on getting real use out of it. That's a present-tense sentence, not a past-tense one.

But here's what I could do with it — and this is the part that matters.

I took the concept and shaped it down. The core idea in Hermes is an agent that lives outside the work and talks to you about it. I lifted exactly that into Trident Forge and deliberately watered it down: not an assistant, not a general-purpose second brain, just an agent whose entire job is telling me what the system is doing. State. Health. What fired, what didn't, what's about to. It sits beside the trading system and reports on it — it never touches the path. Ninety percent of the original idea got cut, on purpose, because ninety percent of it wasn't what I needed.

That cut is the whole argument for building my own, in the shape I built it.

You cannot make that cut from inside somebody else's product. You take the tool on its terms — its scope, its surface, its idea of what you must want — and if what you need is a tenth of it wired somewhere it wasn't designed to go, the answer is no. Owning the layer meant I could keep the idea and leave the rest.

Renting isn't the wrong call; it's the right one for plenty of people. But not everyone works the same way, and cutting a good idea down to the size of your actual problem is not something to be nervous about doing.

## What I built instead

Not out of principle. Because those specific levers were the ones I needed my hands on.

**Every child prompt is bounded.** Anything I dispatch to an agent carries the same three things: explicit SCOPE — which files and directories are actually in play — a smallest-sufficient-change instruction, and a named stop condition drawn from a fixed set of terminal states. Five named ways a run is allowed to end, and it has to end in one of them. Success. No-op. Blocked. Stalled. Exhausted. An agent that can't name which one it hit hasn't finished; it's just stopped talking.

**Two phrasings are banned at the template level.** *Develop and compare several approaches* and generic *think deeply* padding. Both are measured waste [1] — roughly 15× and 1.6–2.2× the reasoning tokens, with no accuracy gain either time. Banning them in the template means that tax gets paid zero times instead of every time. Effort comes from choosing the model tier, not from stacking adjectives onto a prompt. Surgical changes, applied to prompts instead of diffs.

**Fan-out is a design decision, not a reflex.** Past roughly five concurrent agents, orchestration stops being free — a Dispatch or Conductor run gets a gap-check first, and the result gets reported as a terminal-state tally rather than a vibe.

**Memory is mine to read and edit.** Plain Markdown, greppable, wrong facts fixed by editing a sentence. There's a linter that catches the mechanical failures — dangling wikilinks, index drift, stale dates — at zero token cost, before I spend a model on the judgment calls. Covered fully in the last field note; it's the load-bearing piece.

**Nothing ships on a claim.** A verifier — a separate agent whose only job is to try to break the claim that the work is done — runs against any diff touching live money, the exit path, or the risk engine, and its default stance is FAIL. An error is never reported as success. Nothing gets marked complete without the test output to prove it.

That last one isn't a productivity preference. It's the difference between a system that tells you what happened and a system that tells you what it hoped happened.

None of the above is model work. All of it is harness work — and all of it was reachable only because the harness is mine.

## Where this stops being an opinion

The argument stops being abstract the moment there's live money in it.

My own doctrine took me a year and some expensive lessons to arrive at: **no LLM anywhere in the execution path.** The model does its work offline — building the strategy, tuning it, arguing with me about it. Then it gets out of the way. What actually touches the market is deterministic, inspectable, and boring on purpose. Risk gates that don't negotiate. Breakers that survive a restart.

Why that boundary is non-negotiable is a whole field note on its own — what actually breaks at the moment it gets crossed, and what learning that cost me. That one's coming.

This is the seam the Trident Digest lives in — a monthly I'm starting on exactly this question: why automated trading is about to get more prevalent, and more capable, faster than most people expect, and, from where I sit, what's actually worth doing and what to stay clear of. If the execution-path line above is the kind of thing you want more of, that's where it'll be.

That's a harness position, not a model position. It doesn't say the model is weak. It says the model belongs in the design loop and not the execution loop, and the boundary between those two is something the harness enforces — or fails to.

I read other builders' systems on purpose. Not for reassurance — for pressure. Somebody else's architecture is the cheapest way I know to find out whether mine survives contact with a mind that never talked to me.

Sequence matters here, so I'll be exact about it. I'd already fought my way to that doctrine — in futures, alone, over a year of expensive lessons — before I ever found the system I'm about to describe. It didn't teach me the shape. It showed up afterward and had independently landed on it.

Polybot [3] is an open-source Polymarket trading infrastructure and strategy reverse-engineering toolkit — MIT-licensed, Java 21 microservices, built by a developer going by ent0n29. Different market. Different asset class. Different language, different stack, different everything. No contact, no shared lineage, no common influence I can find.

It lands in the same four places mine did.

There is no LLM in the execution path. The strategy is built and tuned offline, and the split is structural rather than stylistic — the repo separates a strategy service from an executor service, so the thing that thinks and the thing that fires are different runtimes. The risk gates are deterministic. The breakers survive a restart.

Two builders, working alone, in markets that share nothing except the fact that a wrong order costs real money — and the same four load-bearing decisions.

That convergence is the argument, and the argument isn't that I was right. Taste diverges. Put two builders on one problem with free rein and you normally get two systems that don't resemble each other, because architecture is where personality leaks out. When independent solutions converge anyway, the shape isn't coming from either builder. It's being dictated by the problem.

So the doctrine stands on its own feet, not on mine: intelligence in the design loop, not the execution loop. The model does its work offline; the thing that touches live money is deterministic and inspectable. I didn't arrive there because it's elegant. I arrived there because the problem doesn't leave much else standing — and somebody I've never met got pushed to exactly the same place.

## What owning it costs

I'd rather say this plainly than let you discover it at 1am.

Owning your harness means maintaining it. Debugging it. There's no vendor to escalate to, no status page, no support thread where someone's already on it. When it breaks at one in the morning, it breaks in code you wrote.

And ownership doesn't prevent rot — the 62.8% cut in the last piece was entropy that accumulated in a harness I own completely. What ownership gave me was somewhere to stand while I measured it.

Most people shouldn't do this. If your work lives in one tool, on one machine, and mostly looks like conversation, the rented harness beats what you'd build, and it beats it on day one instead of month six. Building your own scaffolding on principle when a product would do is an elaborate way of not shipping.

Here's my line.

I own it because the failures that were actually killing me lived in the harness — and I'd rather be able to reach them.

That's the whole calculus. Not that owning it is virtuous. It's a maintenance bill, and I pay it monthly. But when the failure sits in a layer you don't control, your only remaining move is to wait for someone else's next release and hope it happens to help.

## Landing

Back to the original suspect.

The model is rented. It'll be a different one next quarter, and that's the good part — it improves without me, on someone else's schedule, at someone else's expense. I don't want to own it.

The harness is the part that stays. It holds your memory, spends your tokens, shapes every prompt you send, and quietly decides how much of your work survives the session.

Build the part you keep.

---

## References

[1] *Prompt-Induced Waste.* arXiv:2608.01347. — Source for the 5–30× harness cost variance, the 16,000–20,000-token re-transmitted prefix, the ~15× cost of "develop and compare several approaches," the 1.6–2.2× cost of generic "think deeply" padding, and the 2.61× cost of a misleading architectural hint.

[2] *Model or Harness?* arXiv:2607.28802. — Source for the harness-vs-model fault taxonomy, the `comp1—comp2 · fault:side` labeling convention, and the seven memory failure modes.

[3] ent0n29. *Polybot — open-source Polymarket trading infrastructure & strategy reverse-engineering toolkit.* GitHub, MIT license. https://github.com/ent0n29/polybot — Source for the independently-converged architecture: no LLM in the execution path, offline strategy construction with a strategy service separated from an executor service, deterministic risk gates, and restart-surviving breakers.

---

*Subscribe below, or find me on Threads.*

— *Thomas Adair. Marine. DJ/Producer. Systems Architect — shipping across trading systems, music production, agentic tooling, and consumer apps with AI orchestration.*
