---
title: "The Expected Outcome Reframe: How I Get Unstuck"
slug: "expected-outcome-reframe"
excerpt: 'Reframing "I want to build X" as "the expected outcome is Y, verified by A, B, C" — and the different methods that got me unstuck.'
tags:
  - AI
  - solo-builder
  - field-notes
  - systems-architecture
  - AI-orchestrated-development
feature: false
ready: true
---

<!-- CTA/VOICE PASS 2026-08-11 — REFINED DRAFT, NOT FOR PUBLICATION AS-IS.
     SEQUENCING CONFLICT — read this first: the original draft is subtitled "First in a
     series" and lists "the persistent memory bundle" as an UPCOMING piece. In the locked
     queue, the memory bundle ships first and this ships second. This draft is rewritten
     for the locked order (memory piece already out). If you'd rather keep the original
     framing, renumber instead. See CHANGELOG.md. Resolve all [AUTHOR: …] markers. -->

**By Thomas Adair.** Marine. DJ/Producer. Systems Architect — shipping across trading systems, music production, agentic tooling, and consumer apps with AI orchestration.

*Field notes on what actually works.*

---

## The wall

I have hit the same wall on projects that had nothing to do with each other.

Different domains, different tools, same shape. Something works once and never again. Something gets most of the way there and stops. I come back a week later and I am not certain which of my own previous attempts I already tried … so I try one of them again.

That is not a tools problem — I had the tools. It is not a capability problem either; the code ran, the systems held, the parts I built did what I built them to do. What I did not have was an **expected outcome**. A sentence that says what *done* is, in terms I can check without asking myself how I feel about it.

Without that sentence, every work session is an exploration. With it, every work session is a verification pass.

That difference is the whole article.

## The reframe

The stuck framing is always some version of this:

> *I want to build X.*

There is nothing in that sentence to close against. You try something, you look at it, you decide it is not right, you try something else. Progress becomes a feeling, and feelings are terrible instrumentation.

The reframe:

> *The expected outcome is Y, and I can verify it by A, B, and C.*

The second sentence does something the first cannot. It splits one vague ambition into a short list of binary questions. Either A is true or it is not. Either B is true or it is not. Once the questions are binary, you have a plan — because a plan is just an ordered list of checks with the fixes wedged in between them.

It is a small edit on the page. It is enormous downstream.

## Writing the sentence

Here is the part I skipped for a long time, and the part that decides whether the reframe does anything for you: most people write the reframe and get a second vague sentence.

*"The expected outcome is that the memory system works well."* That is "I want to build X" wearing a lab coat.

Three tests, and Y has to pass all three.

**Someone else could run the check.** Not "I'll know it when I see it." If I handed the check to a stranger with no context, could they run it and come back with a yes or a no? *"A cold session can state where a project stands"* survives that. *"The memory system works well"* dies on it instantly.

**The check has an observable read-back.** There is a thing you look at — a session's answer, a number in a file, a log line. If you can't name what you'd look at, you don't have a check; you have an intention.

**Failing is possible, and you can say what failing looks like.** This is the one people skip. If there is no state of the world where the check comes back false, the check is decoration. A target that cannot fail cannot tell you anything when it passes.

Run a candidate sentence past those three and it either survives or it collapses. When it collapses, the collapse is informative — it usually means you don't actually know what you're building yet, and the honest next move is another hour of exploration rather than a fake target.

## Where I learned it: the thing that kept forgetting

The project that taught me this was not a project. It was the substrate underneath all of them — the memory bundle I wrote about last time.

Here is the problem as I actually lived it. I would open a session with an AI, explain the entire system from the beginning, get real work out of it, close the session, and lose everything. Next day, same explanation. Then the tooling generation turned over — I tried OpenClaw, then MoltBot, then landed on Hermes, which stuck — and every time, the thing I lost was identical. Everything the last version of me had worked out.

I never quit on that problem. I also did not solve it for a long time, and the reason is embarrassing in hindsight: I was framing it as *I want the AI to remember things.* That is an "I want to build X" statement wearing a technical costume. It has no closable endpoint. There is always a longer context window next quarter, a better opening prompt, one more tool worth trying.

So I wrote the other sentence down:

> *The expected outcome is that a cold session — new, on any machine I own, with no prior context and no explanation from me — can state where a project stands and what I have already corrected it on. I verify it by opening a cold session and asking.*

Now the move that actually generates the plan, because "checkpoints fall out of it" is the kind of thing people say when they've stopped noticing what they're doing.

You take the outcome sentence and you break it at every clause that has to be independently true. Each clause is a place the sentence can fail on its own. *A cold session* — so the knowledge has to survive the session that made it. *With no explanation from me* — so a new session has to find it unprompted. *Where a project stands* — so it has to be current, not merely present. *On any machine I own* — so it has to be reachable from a box that never wrote it.

Four clauses, four checkpoints:

1. The knowledge exists somewhere outside any individual session.
2. A new session can find it without being told where to look.
3. It is current — it matches what is true today, not what was true in April.
4. The check still passes from a machine other than the one that wrote it.

That is the whole trick, and it is mechanical rather than clever. The checkpoints were already in the sentence. Writing the sentence carefully is what puts them there.

Every layer of what I ended up building exists because one of those four came back false. And each one needed a **different method**, which is the part I want to put weight on.

**Checkpoints one and two came back false first, so the method was files.** A directory of small Markdown notes with an index at the top. I did not invent the shape — Andrej Karpathy published a pattern for an LLM wiki, an index plus small linked articles, and that gist is the direct ancestor of what sits on my disk. What I changed was the typing, because my failures were typed. "It forgot something" was never one problem. Forgetting who I am, forgetting a correction, forgetting where a build stands, and forgetting a paper I meant to keep are separate failures that have to be findable by kind. So every file carries a type, and the types *are* the failure classes.

**Then checkpoint three came back false, and no amount of more files fixed it.** I had notes that were technically present and quietly wrong — a rule that was correct in April, followed dutifully in July, producing work that was confidently obsolete. Files do not create memory. What creates memory is writing things down at the moment they happen, in the format that will be consultable later. That is not a file problem; it is a cadence problem, and the method for it is discipline, not architecture. The rule I actually hold myself to: if I have to correct the same behavior twice, the second correction is a bug in my memory system, not a bug in the model.

**Then checkpoint four came back false, and the method changed again.** The files solved session death. They did not solve *me* — I work across a desktop and a laptop, and the sessions that mattered were not always on the machine holding the notes. I already had a VPS running around the clock for the trading system, so the durable box was sitting there either way. Putting a shared record on it was less a design decision than noticing the obvious.

Files, then discipline, then portability. None of them was the idea I started with, and none of them would have been enough alone.

## Which method, and how you know

Three different methods in a row is not luck, and it is not taste. Looking back at the three, the failing check told me which family to reach for — and the tell is the *shape* of how the check failed.

**The thing isn't there.** Nothing to read, nothing to point at. The method is construction: build the artifact. Checkpoints one and two.

**The thing is there and it's wrong.** The artifact exists, a session reads it, and the answer is confidently stale. Building more artifact makes this worse, not better — you get more wrong things. The method is cadence: change *when* and *how often* you write, not what you write into. Checkpoint three.

**The thing is there, it's right, and it can't be reached.** Correct in one place, absent in another. Not a content problem at all. The method is transport: move it, mirror it, serve it. Checkpoint four.

I did not have that rule when I was living it — I found each method by walking into the wall it was shaped like. But it holds on every case I can find in my own work, and it is the difference between trying variations and changing weapons. <!-- [AUTHOR: this three-shape rule is INFERRED from your three cases. It's the highest-value addition in the piece if it's true, and the most dangerous if it isn't. Check it against a fourth case — the Trident v2 migration below, or anything else — before you publish it as a rule. If it only fits these three, demote it to an observation about these three.] -->

That is what changed for me. Persistence stopped meaning *try the same thing again, harder* and started meaning *which check failed, and what shape did the failure have?* The first version of persistence is stubbornness. The second one compounds.

## When the target is the thing that's wrong

There is a failure mode inside this method and I would rather hand it to you than let you find it the way I did.

Sometimes a checkpoint refuses to go green no matter what method you bring to it, and the reason is not the method. It's the checkpoint. The target was wrong — I wrote a verification I couldn't actually reach, or I wrote one that measures something adjacent to what I care about.

The tell is specific: two or three genuinely different methods, aimed at one check, all failing in different ways. Same method failing three times is a method problem. Three different methods failing is a target problem, and grinding a fourth method against it is the exploration trap wearing verification's clothes.

The fix is not to lower the bar. It's to go back to the outcome sentence and ask which clause I wrote wrong … then rewrite the sentence and regenerate the checks from it. Rewriting the target feels like cheating the first time you do it. It is not. Refusing to rewrite a target you already know is wrong — THAT is the cheat, and it burns weeks.

## The second one, briefly

The same reframe unstuck something much larger and much slower.

Early on I compiled a signal pipeline I called the Prop Relay — strategies written in Pine Script, wired through TradersPost, into a prop-firm account. It worked, and it was the catalyst for the bigger system I built next, Trident Forge. I kept developing that system until I hit a conclusion I did not want: it needed a rethink, not another patch cycle. That decision started version two.

The old framing was *I want to migrate my live strategies to v2.* No endpoint. Weeks of work with no way to say whether the week counted.

The new framing: *the expected outcome is a set of accumulated parity days at a profit factor above a stated floor, with an information-coefficient half-life above a stated floor, verified by a parity register that compares v2's output to v1's output on identical historical data.* <!-- [AUTHOR: "a stated floor" twice is the essay hedging where the essay is arguing against hedging. Either name the two numbers, or say in one clause why you're not naming them — a reader will notice that a piece about writing checkable targets declines to show its own. Naming them is stronger.] -->

That is a great deal more arithmetic than the memory problem, and it is the identical move. Old framing, no closable endpoint. New framing, a specific file with specific numbers to hit. The register had to be designed before it could be used, which is real work — and that is the honest cost of this method, not a footnote to it. Sometimes the verification is a bigger build than the thing you were trying to verify. You pay it anyway, because the alternative is paying for weeks you can't account for.

Since the reframe, the question *am I making progress?* has stopped costing me anything. Progress is a number now. The number either moved or it did not.

## Why this generalizes

The pattern behind the failure is not specific to any tool, any language, or any domain.

1. A project starts with "I want to build X."
2. Nobody ever articulates what *built* means in verifiable terms.
3. Sessions proceed as exploration — try, look, judge, try again.
4. There is no closable loop, because there is no target to close against.
5. The project sits at "almost working" for weeks or months.

The way out is available at any point, from any position, and it is short enough to write on the back of something:

> *Not: "I want to build X."*
> *Instead: "The expected outcome is Y, and I can verify it by A, B, C."*

Then three questions you could not ask before:

- What are the checkpoints between where this actually is and the expected outcome?
- Which checkpoints are already true? Which are not?
- For each false checkpoint, what is the fastest read-back that tells me?

Those questions produce plans. Plans produce diagnostics. Diagnostics produce specific problems. Specific problems get fixed — and when one of them refuses to be fixed the way you first attacked it, you now know exactly which checkpoint to bring a different method to.

That is the repeatable part. It is not talent and it is not tooling. The transformation is from **exploration** to **verification**. AI makes verification faster once you know what you are verifying. The reframe works without it.

## The trap it walks you past

The default mode for creative and technical work is exploration, and that is not a bug. Exploration is how you find out what you want to build in the first place. The mistake is not exploration — it is *staying in exploration after you already know*.

My own tell is simple. If I can describe what I want to a friend in twenty seconds, I can write the expected outcome in one sentence. And if I can write it and I have not, I am not exploring anymore. I am procrastinating on the verification loop.

The reframe hurts a little the first time. It closes doors. It says *we are not redesigning this anymore, we are checking whether the thing arrives.* It commits.

That commitment is what makes the loop closable. Everything downstream — the checks, the plan, the varied methods, the fix — follows from committing.

## What I am not claiming

This is not a controlled experiment. N equals one solo builder. My evidence is the past year of my own work, and I have no comparison group and no significance test to offer you.

The reframe was not invented here, either. Any engineering discipline that talks about "definition of done" is pointing at the same thing, and acceptance criteria in agile shops are the same move with more ceremony around it. The specific formulation — expected outcome plus verification checkpoints, plus *change the method when the check shape changes* — is what worked for me building alone with AI as the force multiplier. The public FABLE PROTOCOL document I read after adopting it has language aimed at the same discipline. Plenty of other builders have almost certainly arrived here on their own.

What I am claiming is narrower and I will stand behind it: if you are sitting on a project that has been at "almost working" for weeks, the reframe is available to you, it costs one sentence, and it works.

## What's next

More field notes are coming. In order:

- Tiered model routing with hard carve-outs — when to use the strongest model, when to use the cheapest, and which layers never route down.
- Plan with the strong model, build with the medium one — the cost multiplier of separating deep-context planning from durable-artifact execution.
- The verify gate — pre-deploy insurance for AI-generated code, structured so it does not become a permanent blocker.
- The three-attempts rule — when to stop trying variations of a fix and admit the approach itself is wrong.

If you are building alone with AI, or you want to be, I would like your company. Subscribe below, or find me on Threads.

— *Thomas Adair. Marine. DJ/Producer. Systems Architect — shipping across trading systems, music production, agentic tooling, and consumer apps with AI orchestration.*
