# CTA + Writer-Voice Pass — 2026-08-11

Refined drafts for Thomas's final authoring pass. **Nothing here is publish-ready.**
Originals in `queue/` and `drafts/` are untouched.

Two lenses applied to each piece:

- **A — Cognitive Task Analysis.** Interrogated each essay the way CTA interrogates an
  expert's self-report: assume the author omitted the decisions that have become
  automatic. Hunted for imperatives with no cue, claims with a missing "why," thresholds
  asserted without a value, and steps that only work because the author already knows
  something the reader doesn't. Where a gap needs a fact I don't have, it's marked
  `[AUTHOR: needs X]` as an HTML comment — invisible if accidentally rendered, greppable
  before publish.
- **B — Writer voice.** Rhythm audit paragraph by paragraph (short / long-developing /
  short), em-dash and ellipsis presence in any prose run over ~200 words, numeric-flex
  removal, cliché and hedge removal, present-tense observation, first-person ownership,
  beat-landing closes. Cadence and idiosyncrasy preserved on purpose — sharpened, not
  smoothed.

**Before publishing any of these: `grep -n "AUTHOR:" drafts/cta-voice-pass-2026-08-11/*.md`**
and resolve every hit. Then strip the `CTA/VOICE PASS` header comment from the top of
each file.

---

## Lead-article adjudication — queue/01 vs drafts/01-REWRITE

**Verdict: the REWRITE wins, decisively. Ship it as the lead, with three grafts back from
the queue version.** The refined `01-persistent-memory-bundle.md` in this folder is that
merge.

### Why the REWRITE wins

1. **It has a counterargument section and the queue version doesn't.** "The easier paths"
   names the vendor-memory objection, concedes it honestly for the reader it actually
   applies to, and *then* draws the line at ownership-vs-convenience. The queue version
   never acknowledges that an easier option exists. That single section is the difference
   between an essay and a testimonial — and it's the piece's strongest writing.
2. **It already obeys the numeric-flex rule; the queue version violates it repeatedly.**
   Queue: "hundreds of session terminations, dozens of model rotations," "about two
   hundred more files," "four hours," "five to ten substantive exchanges." Rewrite:
   "a good many more," "an afternoon," "every few substantive exchanges." The rewrite is
   what the voice calibration asks for, without being asked.
3. **Rhythm.** The queue version runs long and even. The rewrite breaks — "That's it.
   That's the whole shape." / "Here's the line." / "The bundle solved session death. It
   did not solve me." It has a pulse; the queue version has a pace.
4. **The mechanism gets a reason, not just a description.** Rewrite explains *why*
   fail-soft matters ("a memory system that can halt the work is a memory system I'd stop
   using by Thursday"), *why* the index ceiling is the worst failure ("nothing errors, and
   nothing warns you"), *why* typing matters ("if you can't tell them apart you can't fix
   any of them"). The queue version asserts the same facts without the why.
5. **The Karpathy credit lands.** Queue: a slightly stiff two-sentence disclaimer.
   Rewrite: "He gave the shape away for free. I'd rather say his name than quietly absorb
   it … so: thank you, Andrej." That's the voice.
6. **The close is stronger.** "Not a demo, not a benchmark — an absence. The re-briefing
   that didn't happen." The queue version's equivalent beat is buried mid-paragraph.

The queue version's only real advantage is length — it's ~1,950 words to the rewrite's
~2,750. If the constraint is a short lead post, that's an argument. It is not an argument
about quality.

### What got grafted back from the queue version

- **The handoff threshold.** Queue names a specific percentage; the rewrite softened it to
  "the handoff rule." A threshold is an operational cue a reader can use, not a flex —
  restored as a placeholder with an `[AUTHOR]` marker to put the number back.
- **"the types *are* the failure classes"** compression — present in both, kept in the
  crisper queue phrasing.
- **The "one VPS reboot cycle" style of concrete survival evidence** — deliberately *not*
  grafted. It's flex, and the rewrite is right to have cut it.

---

## 01 — The Persistent Memory Bundle (merged lead)

Base: `drafts/01-persistent-memory-bundle-REWRITE-2026-08-04.md`.

### CTA — what tightened

- **The load-bearing mechanism is missing and nothing else in the essay works without
  it.** "Every session opens it first" is the sentence the entire architecture rests on,
  and the essay never says *how* a session is made to open it. A reader who copies the
  folder gets nothing. Flagged with an `[AUTHOR]` marker; this is the highest-priority
  gap in the piece.
- **The write rule had no threshold, and the missing threshold causes a cost the essay
  names later.** Rule one says write a feedback memory when a session "corrects a class of
  behavior" — with no test for *class*. Added the test (would I give this correction again
  next week, on a different task, in a different repo?) and, more importantly, connected
  it explicitly to the index-bloat cost in "What it costs." Those two sections were cause
  and effect and the essay presented them as unrelated. That link is the single best CTA
  find in the piece.
- **Type selection had no tie-breaker.** A correction about a specific project is both
  feedback and project. Added the generalizes-past-this-build tie-breaker and both novice
  failure modes (burying a standing rule; promoting a one-off to a law). Marked INFERRED —
  confirm or replace.
- **Update-vs-create was absent entirely.** The rule that prevents three files
  half-remembering the same thing. Added.
- **No standard of "good" for a memory file.** Added the cold-session-actionability test.
- **Layer two had no routing rule.** Two stores, and the essay never says what goes in
  which. Added a blast-radius split, marked INFERRED, with the duplicate-fact warning.
- **Fail-soft's cost was unstated.** A session running on a stale local bundle produces
  work that looks identical to good work. Added, with an `[AUTHOR]` on whether the
  fallback actually surfaces in-session today.
- **Silent index overflow had no detection cue.** The essay says it fails silently and then
  says "I hit that ceiling again recently" — which implies a detection method the reader
  never gets. Added the tell, with an `[AUTHOR]` asking whether a mechanical check exists.
  If it doesn't, saying so is stronger than implying it does.
- **"current-truth prose" needed one clarifying step** — that it's a snapshot, not a
  changelog, and why a project file that grows into a log stops being read.
- **No falsifier for the central claim.** Added a short passage naming what would show the
  architecture is at fault rather than the discipline. This turns the anecdotal proof from
  a testimonial into an argument.

### Voice — what changed and why

- Rule count "Four rules govern the cadence" → "The rules that govern the cadence are all
  scar tissue" (numeric flex; the list is right there).
- Rhythm inserts around the new CTA passages so the additions carry pulse rather than
  reading as bolted-on spec text: "New files are for new subjects." / "That's the actual
  argument." / short beats after long developing sentences.
- Ellipses and em-dashes preserved from the rewrite; the new passages carry their own.
- One ALL-CAPS emphasis was *not* added here — the piece's register is quieter than 02/03
  and it would read as borrowed. Left alone deliberately.
- Close untouched. "The rest of what I build sits on top of this. / More field notes to
  follow." lands; don't move it.

---

## 02 — The Expected Outcome Reframe

### ⚠️ Sequencing conflict — decide this first

The draft is subtitled *"First in a series of field notes"* and its "What's next" section
lists **"The persistent memory bundle"** as an upcoming piece. In the locked queue order,
the memory bundle publishes **first** and this publishes second. As written, piece 02
promises a piece that already went out.

I rewrote for the locked order — subtitle changed to "Field notes on what actually works,"
and the memory section now refers back ("the memory bundle I wrote about last time"), with
the bundle removed from the What's-next list. **The alternative is renumbering** so this
goes first. Your call; the drafts as they stand assume the locked order.

### CTA — what tightened

- **The essay's core instruction had no procedure.** Everything rests on writing a good
  expected-outcome sentence and the piece never says how, which means most readers write a
  second vague sentence and conclude the method doesn't work. Added a **"Writing the
  sentence"** section with three tests: someone else could run the check; there's an
  observable read-back; failing is possible and you can describe it. The third test is the
  one nobody applies — a target that can't fail tells you nothing when it passes. The
  criterion was already latent in your own opening ("in terms I can check without asking
  myself how I feel about it"); this promotes it from an aside to the method.
- **"Four checkpoints fall out of that immediately" — they don't.** That's the expert's
  automated step, and it's exactly the kind of thing CTA exists to recover. Added the
  actual generator: break the outcome sentence at every clause that has to be
  independently true; each clause is a checkpoint. Then showed the four clauses mapping to
  the four checkpoints. This is mechanical and teachable, where the original was magic.
- **Method selection was entirely tacit.** The piece's best insight is "bring a *different
  method* to the failed check" — and it never says how you pick. Extracted a three-shape
  rule from your own three cases: *not there* → construction; *there and wrong* → cadence;
  *there, right, unreachable* → transport. Marked INFERRED with an `[AUTHOR]` asking you to
  test it against a fourth case before publishing it as a rule. **If it only fits these
  three cases, demote it to an observation** — a rule that doesn't generalize is worse than
  no rule.
- **No stop condition — the method had no recovery path.** What happens when a checkpoint
  refuses to go green because the *checkpoint* is wrong? Added "When the target is the
  thing that's wrong," with the tell (three genuinely different methods failing three
  different ways = target problem, not method problem) and the fix (rewrite the sentence,
  regenerate the checks). Without this, the reframe has a failure mode that looks exactly
  like the exploration trap it claims to cure.
- **The v2 example hedges where the essay argues against hedging.** "A stated floor" twice,
  in a piece about writing checkable targets. Flagged with an `[AUTHOR]` — name the numbers
  or say in one clause why you won't. A reader *will* notice.
- **The cost of verification was hidden.** Added the honest note that the parity register
  was a bigger build than some of what it verified, and that you pay it anyway.
- **"I have not lost a single week to the question"** — reworded to a claim that's actually
  checkable rather than an absolute.

### Voice — what changed and why

- Subtitle and What's-next reworked for the sequencing fix (above).
- "eighty percent of the way there" → "most of the way there" (numeric flex, and the
  number isn't doing work).
- Ellipsis added — the piece had zero across ~2,100 words: "…so I try one of them again"
  and "which clause I wrote wrong … then rewrite the sentence." Both at genuine
  thought-turns rather than decorative.
- One ALL-CAPS: "Refusing to rewrite a target you already know is wrong — THAT is the
  cheat." Earned; it's the sentence the section exists for.
- Pulse work in the new sections — the three tests are deliberately short-long-short so
  they don't read as a bulleted spec.
- "Three methods, in sequence" → "Files, then discipline, then portability" (count removed,
  and the naming is stronger anyway).
- Close untouched.

---

## 03 — Adversarial Dynamical Systems

### CTA — what tightened

- **The essay's central transfer is never argued.** The paper is about *deliberately
  constructed* adversarial systems. Markets are not constructed by anyone to defeat
  learning. Every practical claim in the piece depends on carrying the result across that
  gap, and the original crosses it silently. Added a full section — **"Does the proof reach
  the market?"** — that (a) states the objection at full strength, (b) says plainly that
  nothing licenses the transfer automatically, (c) offers the actual argument: the
  construction is a *proof device* that removes the excuse "smooth and low-dimensional and
  I have lots of data," and markets reach the same neighborhood by a different mechanism —
  continuous selection pressure from participants whose function is to find and destroy
  exploitable structure. Then bounds the claim: **the paper removes an excuse; it does not
  prove any specific strategy is doomed.** This is the most important change in the pass.
  Without it, a hostile reader dismantles the piece in one paragraph.
- **"Definitionally, exposed to less hard-case risk" was an assertion doing an argument's
  job.** Added the why: the impossibility result blocks extraction of *forecastable
  structure*; a market maker is paid for absorbing inventory and selling immediacy, which
  exists whether or not the price series is learnable. The ceiling and the revenue source
  are aimed at different things. This is the load-bearing inference of the whole piece and
  it was one word.
- **The 50% number is the most misreadable sentence in the essay.** A reader will carry it
  out as "your model wins half its trades." Added an explicit warning paragraph and an
  `[AUTHOR]` marker to name the exact quantity and task in the paper's own terms.
- **The practical question is posed and never answered.** "Which side of the line is my
  strategy on?" Added a **"Which side is this strategy on?"** triage with four questions —
  does it need to forecast a trajectory; is there a mechanism independent of the pattern;
  would degradation show up in the mechanism or only in the P&L; how many other people can
  run this. The cues were scattered through your own prose; this collects them into
  something a reader can run on Tuesday. Then applied it to the pattern strategy in the
  portfolio section, which it fails on all four — makes the example do double duty.
- **The promotion bar and demotion trigger are the essay's entire practical payload and
  neither is specified.** "Strict promotion bar," "extended live-shadow observation,"
  "diverges from validated behavior" — no duration, no criteria, no threshold. Flagged with
  the largest `[AUTHOR]` block in the pass, listing the three things a reader needs. If some
  of it is deliberately unpublished, saying that is stronger than leaving the shape of a
  rule where a rule should be.
- **"until three weeks ago" will rot.** The paper is dated July 14, 2026; this publishes
  weeks later on a queue. Changed to "until this summer."
- **The LLM synthesis skipped its middle step.** "No amount of retraining closes the gap
  from the inside" — added the two-step why: if the drift is architectural the fix must
  come from outside, and the only rewrite loop available *is* outside, so the correction
  can never be self-originating. Also flagged that the synthesis is yours, not the paper's,
  and should carry an explicit marker the way your other claims do.
- **Em-dash name convention**: "Colbrook-Mezić-Stepanenko" → en-dash "Colbrook–Mezić–
  Stepanenko" (author-pair convention, not a hyphenated name).

### Voice — what changed and why

- Ellipsis added — the piece had zero across ~4,300 words: "…a very large lightbulb went
  off" (a genuine beat you'd hit out loud) and the new close.
- "more than a thousand simulated trades" → "a large simulated sample" (numeric flex; the
  count isn't load-bearing and the audit finding is the point).
- Long flat paragraphs in the portfolio section broken for pulse — the market-maker
  paragraph was doing three jobs in one block and now does them in three.
- New close beat added above the CTA-to-subscribe: *"The proof doesn't tell me my
  strategies are doomed. It tells me which of my confidences were free … and which ones I
  actually paid for."* The original close ends on a subscribe line; the piece deserves a
  landing before the ask. **Cut it if it reads as too neat** — it's the one addition in the
  pass that's pure voice with no CTA justification.
- Balanced argumentation was already right (praise the paper → critique the claims →
  close on permission rather than caution). Left structurally alone.

---

## 04 — The Kill Path Shares Fate with the Pay Path

This piece was already the most rigorous of the four — it carries its own confidence tags,
footnotes with primary sources, a method postscript, and a position disclosure. The pass is
surgical. **All six original findings, all confidence tags, and all footnotes are
preserved unchanged.**

### CTA — what tightened

- **5.1 — "a separate channel" is where the argument stops, and stopping there leaves the
  hole open.** An out-of-band revocation still has to reach an executor that sits on the
  pay path; if the channel is down, separation buys a cleaner postmortem and nothing else.
  Added the step that closes it: **invert the default.** The executor requires a positive,
  recent liveness token to keep spending — spend-only-while-permitted, not
  stop-when-told. Losing the channel halts spending because permission expired, not
  because a stop arrived. Named it as the dead-man's switch it is, and named the real cost
  (fail-closed can stop legitimate spending) rather than pretending it's free. This makes
  the title claim *actionable* instead of merely diagnostic.
- **5.3 — the obvious counterattack was unanswered.** If revocation isn't scored,
  revocation is a denial-of-service vector. Added the precise distinction —
  **authenticate, don't score** — and the argument that settles it: asymmetry of
  consequences. A wrongly-accepted revocation stops spending that should have continued
  (recoverable). A wrongly-blocked revocation continues spending that should have stopped
  (gone, at machine speed, with valid signatures). Same asymmetry as exits.
- **5.4 — two things must be pinned down and neither is.** (a) *Who is the principal?* The
  original slides person → household → firm in one sentence; a household is multiple
  identities sharing a bank account, and AP2's mandate chain appears to run
  principal-to-agent with no multi-identity principal. Aggregate exposure across a
  household isn't unimplemented — the entity doesn't exist in the model. Marked with an
  `[AUTHOR]` to verify against the spec's identity definitions. (b) *Sum of what?*
  Committed ceiling and draw velocity are different numbers with different alarm
  behaviors; watch only one and you either alarm on nothing or miss the spike.
- **5.5 — the section contradicted itself two sentences apart.** "Treat any residue as an
  incident" versus "no individual orphan is worth a dispute." Resolved: the unit of alarm
  is the **rate**, not the event — and added the prerequisite everyone skips, that you
  can't alarm on a rate you never baselined. Ship the alarm before the baseline and it gets
  muted in week two, which is worse than no alarm because it occupies the slot.
- **§4 — the analogy's weak point, turned into the argument's strong point.** Institutional
  mandates are backed by contract law, regulators, licensed counterparties, and settlement
  finality. Agent mandates are backed by a signature. Cryptography proves who said what; it
  stops nothing. So what institutional finance absorbs through law has to be absorbed at
  the agent rung through engineering — which is the case for doing the engineering now,
  while it costs a spec revision instead of a court date.
- **§7 — no kill criteria for the product.** In a piece arguing that a claim is worth what
  its falsifier is worth, the product section had no "what would make me not build this."
  Added three concrete ones (AP2 ships mandated out-of-band revocation; CPs converge on a
  union view; enterprise monoculture solves aggregation). Marked `[AUTHOR]` — it's a strong
  credibility move and also you arguing yourself out of a business in public. Your call.
- **Internal count mismatch fixed.** §5 opens "Mine has four at the top" and then presents
  six invariants (5.1–5.6). Changed to a count-free phrasing, which also removes a flex.

### Voice — what changed and why

- "does five things and refuses to do more" → "does a short list of things and refuses to
  do more" (numeric flex; the numbered list follows immediately).
- One ALL-CAPS emphasis added in 5.1: **spend only while permitted to spend** — set in bold
  rather than caps because the section already carries "EXITS ARE SACRED" and two caps
  treatments in one section cancel each other out.
- New passages written to the piece's existing rhythm — the short declarative landing after
  a long developing sentence ("That inverts the failure." / "Those two errors are not the
  same size.") — so the additions don't read as a different writer.
- Em-dashes and the existing ellipses ("just... vanished") left exactly as they are.
- Close untouched. "Exits are sacred. That travels. / Cheers." is the best signoff in the
  set — don't touch it.

---

## Cross-cutting notes

**Repeated opener across three pieces.** The August-2025 friend / Pine Script / TradersPost
/ lightbulb origin story appears in near-identical form in 01, 02 (as the memory-loss
loop), and 03. Published a week apart to the same subscriber list, the third telling will
read as padding. Not fixed in this pass because trimming it changes what each piece can
stand alone as — flagging it as a **cross-piece decision for you**: keep it full in 01 (it's
the lead and it earns it), compress to one clause in 02, and compress to one clause in 03
where it currently runs a full paragraph.

**"Field notes" subtitle** now appears on 02 and 03 identically. Consider differentiating.

**No facts were invented anywhere in this pass.** Every gap that needed a fact I don't have
is an `[AUTHOR:]` marker. Every inference I made from the text is labeled INFERRED inline.
Three of them — the memory type tie-breaker (01), the local-vs-brain routing split (01),
and the three-shape method-selection rule (02) — are load-bearing enough that they should
be confirmed or replaced before publishing, not just skimmed.
