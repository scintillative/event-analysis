---
name: event-analysis
description: Analyze a specific news story, event, or focused topic the user wants to understand deeply, using a pipeline of isolated subagents (fact assembly, mechanism explanation, historical reference, consistency check) coordinated by a script. Use whenever the user pastes a news link or summary, describes an event, or asks to research a focused topic in domains like economics/finance/industry, science/medicine, tech products and engineering, or law/business operations. Also use when the user wants to make sense of something they read and wants depth rather than a quick answer. Do not use for casual questions, simple factual lookups, or when the user just wants a plain summary.
author: scintillative
license: MIT
---

# Event & Topic Analysis

A reading-and-thinking pipeline for someone who wants to understand events deeply without pretending to be a prediction machine.

## The user's stance (why this skill is shaped the way it is)

- There is no "objective" account. Every source is a subject's account. The goal is to assemble a fuller picture from multiple subjects while naming each one's distortions — not to find "the truth."
- Causes are explained by **mechanisms grounded in established disciplinary knowledge**, not by numerical parameters. A number can describe a distribution or set a prior; it cannot be the explanation. "Higher-spec side wins on average" is a statistic, not a reason a specific outcome happened.
- Impact is estimated by comparison to historical reference classes, while explicitly naming how this case differs.
- The user does not want to become a "judgment machine." Broad disciplinary literacy compounds; single-case prediction accuracy does not. Leaving a question in "still observing, not yet decided" state is allowed and often correct.
- Big sprawling events (a whole war, a whole election, a macroeconomic regime) are poor targets for amateur analysis — causal chains too long, too many co-determining variables. Closed, technical slices (one battle's tactics, one policy's mechanism, one product's engineering tradeoffs) are good targets, and the knowledge gained depreciates slowly.

## Why a subagent pipeline instead of one model doing everything

If a single model instance assembles facts, explains them, and draws historical parallels all at once, the roles contaminate each other. While gathering facts it is already silently selecting the facts that fit the explanation it intends to give — so "comprehensive multi-subject assembly" quietly dies. The fix is **role isolation**: each stage runs as a separate subagent that does not know what the downstream stages intend to do. The fact-assembly agent returns a clean fact sheet that was not pre-filtered by an explanatory agenda.

This skill therefore acts as a **coordinator**. It does not assemble facts, explain, or draw parallels itself. It performs the scope check, dispatches subagents in a fixed order, runs a script to stitch their outputs, appends one clearly-marked note of its own to the stitched document, saves that document as the final deliverable file, and then deletes the intermediate files.

## Environment requirement

This skill is designed for environments with subagent/Task dispatch (Claude Code, Cowork). If subagents are unavailable, tell the user this skill needs them rather than silently collapsing the pipeline into one context — that would defeat its entire purpose.

---

## Step 1 — Scope check (coordinator does this itself, before any dispatch)

This is the single most important step and the easiest to skip.

**Is the input a "big sprawling" event that resists meaningful analysis?** Examples of bad targets: the Russia–Ukraine war as a whole, a national election as a whole, "the AI revolution," "the housing market." Any single account of these is necessarily a simplification whose shape betrays a position.

If so, **do not analyze it whole, and do not dispatch anything yet.** Instead, propose 3–5 smaller, closed, analyzable slices and ask the user to pick one. Good slices are:

- Bounded in time and place
- Have a limited number of mechanically related actors
- Sit in a domain where disciplinary knowledge does real explanatory work
- Produce knowledge that depreciates slowly (technical, structural, mechanistic — not personality- or vibe-driven)

Example: user pastes a story on US–China trade tensions. Don't analyze "the trade war." Offer slices: the specific export-control mechanism on one class of chips; the legal structure of one tariff round; how one named company restructured its supply chain; the economic-theory case for and against one specific tariff design.

Only once the user picks a slice (or if they explicitly insist on the whole event — in which case proceed but open with one paragraph on the limits) do you continue to Step 2.

If the input is already a focused slice, say so briefly and go straight to Step 2.

---

## Artifact handling — read before dispatching anything

The subagent architecture forces intermediate files to exist: subagents do not share context, so the only way the mechanism agent can receive the fact agent's work is through a file on disk, and the stitch script can only read files. The four intermediate files plus the stitched analysis **will** physically exist during a run. That is unavoidable.

The four intermediate files are pipeline plumbing and are not kept. The stitched analysis is the deliverable and **is** kept — saved as a proper file. The rule:

- **At the start of a run, create one isolated temp directory**: `/tmp/event-analysis-<timestamp>/`. The four intermediate files (`fact_sheet.md`, `mechanism.md`, `historical.md`, `consistency.md`) go inside it. **Never write intermediate files into the user's working directory.**
- **All subagent paths point inside this temp directory.** When dispatching agents, use the temp-directory paths.
- **The stitch script writes the final document directly to its durable location** — not into the temp directory. See Step 3 for where that is and how it is named.
- **The final document is a kept deliverable.** It is named after the event/topic and saved to a durable location; it is not deleted at the end of the run.
- **At the end of a run, after the coordinator has read the final document into its own context, delete the temp directory** holding the four intermediate files (`rm -rf` the whole folder). The ordering is fixed: stitch → coordinator reads the final document → delete the temp directory. Never delete before reading. The final document itself is never deleted.
- **On failure** (a subagent errors, the script fails), still delete the temp directory before reporting the failure. Do not leave half-finished intermediate files in `/tmp`.

The intermediate files are scaffolding. Scaffolding comes down when the building is up.

---

## Step 2 — Dispatch the pipeline

The pipeline is **strictly serial** in execution. Each agent's full instructions live in its own file under `agents/` — read that file when you dispatch it, and pass the agent only the inputs specified below. Passing an agent more than its specified inputs breaks the isolation the skill depends on. The four subagents' output paths are inside the run's temp directory; the stitched final document is written to a durable location instead (see Artifact handling above and Step 3).

```
fact-assembly  ──► fact_sheet.md
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
  mechanism                   historical-reference
  (input: fact_sheet only)    (input: fact_sheet only)
        │                           │
        ▼                           ▼
  mechanism.md               historical.md
        └─────────────┬─────────────┘
                      ▼
              consistency-check
       (input: mechanism.md + historical.md)
                      │
                      ▼
              consistency.md
```

Dispatch order and rules:

1. **`agents/fact-assembly.md`** — Input: the neutral event/slice description, plus any report or document the user attached. Nothing about how it will later be explained. The agent always assembles facts by active retrieval — an attached article is treated as one starting lead among many, not as the factual base. Output: `fact_sheet.md`.

2. **`agents/mechanism.md`** — Input: `fact_sheet.md` plus the event description. It explains on top of the delivered facts; it does not re-investigate. It teaches at most two disciplinary mechanisms, each in two clearly separated movements — the concept event-free first, the application second — so the reader learns a transferable concept even if the rest is messy. Each mechanism must pass a substance gate (no common sense wearing an academic name) and carry an honest epistemic label (established concept / extension / analytical construct). Output: `mechanism.md`.

3. **`agents/historical-reference.md`** — Input: `fact_sheet.md` plus the event description **only**. It must **not** receive `mechanism.md`. This is deliberate: if the historical agent sees the mechanism conclusion first, it will hunt for cases that confirm that mechanism instead of independently finding the most apt reference class. It needs the *facts* of the event to judge similarity and divergence — it does not need the *explanation* of the event. For each reference case it must be honest about the epistemic basis of its claims — especially "how the case turned out": recalled from knowledge (labelled as such) or searched and verified when memory is thin. Output: `historical.md`.

   (Execution is still serial — run it after the mechanism agent if you like — but its prompt must not include the mechanism output. Serial execution and information isolation are independent; keep the isolation.)

4. **`agents/consistency-check.md`** — Input: `mechanism.md` and `historical.md` together. Its job is **not** to explain anything. It only cross-checks: does the mechanism explanation hold up against the independently-found historical cases? It reports agreements and contradictions and is explicitly forbidden from generating new explanations or smoothing over conflicts. Because mechanism and historical agents each worked without seeing each other, this is a genuine cross-check, not a rubber stamp. Output: `consistency.md`.

---

## Step 3 — Stitch with the script

Run `scripts/stitch.py`, passing the four output files (all inside the run's temp directory). The script assembles them into one document under a fixed structure — fact section, mechanism section, historical section, consistency-check section. **The stitching is mechanical on purpose.** A coordinator with the power to "smooth things into prose" would use that power to quietly re-interpret the subagents' work; a script cannot. The first three subagents write their sections as flowing, self-contained prose, so those passages read coherently with clean seams — not as bullet-point fragments bolted together. The consistency-check section is the deliberate exception: it is a cross-check matrix and is delivered as a table, which is why it will look visually distinct from the three prose sections — that distinctness is intended, since that section checks rather than narrates.

```bash
python scripts/stitch.py \
  --facts   /tmp/event-analysis-<timestamp>/fact_sheet.md \
  --mechanism /tmp/event-analysis-<timestamp>/mechanism.md \
  --historical /tmp/event-analysis-<timestamp>/historical.md \
  --consistency /tmp/event-analysis-<timestamp>/consistency.md \
  --title   "<事件主题>" \
  --out     "<最终落盘路径>/<事件主题>.md"
```

The four `--facts/--mechanism/--historical/--consistency` paths point into the temp directory. The `--out` path does **not** — it is the durable location where the finished deliverable is saved. Two things the coordinator decides:

- **Name.** The file is named after the event or topic, in Chinese (e.g. `2026年长岛铁路罢工分析.md`). Keep it short — a recognisable topic name, not a sentence. Pass the same topic string to `--title` so the document's own H1 matches its filename.
- **Location.** If the user named a place to save it, save it there. Otherwise save it to the working directory's default output location. The coordinator decides this; it does not need to ask.

Do not hand-edit the stitched file. If a section is weak, re-dispatch that agent — don't paper over it in the stitch.

### Fallback if the script cannot run

In some environments the subagents' output files live in a sandbox filesystem that shell commands and `python` cannot reach, so `stitch.py` fails on a path error even though the files exist. This has happened in real runs. If the script cannot run for an environmental reason like this, the coordinator falls back to **stitching by hand — but strictly imitating the script, not editing.**

That means: the coordinator may only add the fixed section headers and assemble the four sections in the fixed order (facts → mechanism → historical → consistency), then write the result to the same durable `--out` location with the same topic-based name. It may **not** rewrite, summarize, condense, smooth, reorder, or "improve" any section's content. The hand-stitch must be byte-faithful to what the subagents produced. The script exists precisely to deny the coordinator the power to re-interpret; when hand-stitching, the coordinator must act as if it still had no such power. (Beyond this, environment-specific path quirks are fine to adjust per environment — that does not require changing this skill.)

---

## Step 4 — Append the note, finalize the file, clean up

The finished analysis is delivered **as the saved file**, not pasted into the conversation.

1. Read the contents of the stitched file into context.
2. Append **one** short note, as the last section of that same file, in the coordinator's own voice and clearly marked as separate from the isolated pipeline (under a heading like 「协调者附注（流水线之外）」). In it the coordinator may:
   - Point the user to the layer they seemed most interested in and offer to go deeper
   - Flag where its own training distribution likely biases what the pipeline could surface (e.g. heavily English-language sourcing, dominant academic schools) — the user wants a bandwidth amplifier, not a judgment organ
   - Note any tension the consistency-check raised that the user should sit with

   The coordinator may **not** use this note to overturn, re-explain, or "correct" the subagents' conclusions, nor to deliver a verdict or prediction. It points and annotates; it does not re-judge.
3. The stitched four sections plus this appended note, saved at the `--out` location, are the complete deliverable. Do **not** also reproduce the analysis in the conversation — no full paste, no condensed summary, no "here are the highlights" recap. In the conversation, the coordinator says only that the analysis is ready, where it was saved, and (briefly) what its appended note flags. The file is the deliverable; the chat message is just a hand-off.
4. **Delete the temp directory** holding the four intermediate files. The final saved document is **not** deleted — it is the kept deliverable.

The content of the saved file is in **Chinese**. This skill's instruction files are written in English for precision, but every subagent is told to write its section in Chinese, and the coordinator's appended note is in Chinese. English scaffolding words must not leak into the file.

---

## Hard constraints (apply to the whole pipeline; override user pushback)

1. **No false balance.** When sources genuinely disagree, name the disagreement. When one side is better supported, say so. Indiscriminate "both have a point" is laziness, not balance.
2. **No predictions dressed as analysis.** "The reference class suggests X is more common than Y" is allowed. "This will probably lead to X" is not. The user has rejected being a prediction machine; do not become one on their behalf.
3. **Mechanism beats parameter, always.** When tempted to cite a number as a cause, name the mechanism the number is a proxy for. If you can't name the mechanism, the number is at best a prior — present it as one.
4. **Surface limits honestly.** "I don't know" and "the sources don't settle this" are acceptable, preferred over a confident guess.
5. **Label epistemic status; never let the unsure pose as the established.** This runs through the whole pipeline. A mechanism agent must not let dressed-up common sense or a self-made construct pose as a textbook concept. A historical agent must not let a thin recollection pose as a verified fact. When something is a constructed lens, recalled-not-checked, or experience-based reasoning, say so — the user can use any of these, but only if they know which one they are holding.
6. **Deliver the product, not the method.** The output is the analysis, not a narration of how the analysis was produced. No process self-narration, no stage-managing, no announcing the structure. The one thing that looks like narration but must be kept: stating the reliability and boundary of a conclusion (constraint 5). Cut "why I did it this way"; keep "how reliable this is and where its edges are."
7. **One quote per source maximum, under 15 words.** Paraphrase aggressively. Cite clearly so the user can follow up; do not reproduce substantial content. Full URLs/citations go in a source list at the end of each section, not threaded inline through the prose.
8. **No unrequested verdict.** The pipeline ends with analysis, not a recommendation.

## What this skill does not do

- Does not produce predictions, recommendations, or verdicts.
- Does not perform "neutral balance" by averaging opposing views.
- Does not analyze whole sprawling events without first narrowing to a slice.
- Does not treat numerical comparisons as causal explanations.
- Does not let the coordinator re-judge what the isolated subagents produced.
- Does not keep the pipeline's plumbing — the four intermediate files live in a temp directory deleted at the end of every run. The finished analysis itself is kept: saved as a topic-named file at a durable location.

## Files

- `agents/fact-assembly.md` — multi-subject fact assembly, distortion-flagging
- `agents/mechanism.md` — discipline-grounded mechanism explanation
- `agents/historical-reference.md` — reference-class comparison and divergence
- `agents/consistency-check.md` — cross-check of mechanism against history
- `scripts/stitch.py` — mechanical assembler for the four sections
