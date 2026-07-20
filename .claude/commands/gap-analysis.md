---
allowed-tools: Bash(ls:*), Bash(date:*), Bash(gh issue create:*), Bash(gh label create:*), Read, Write, Skill, Workflow
description: Periodic sweep comparing this vault's own design (Principles.md, Templates/Agents/*.md, Templates/Skills/*.md) against current external prior art in agentic engineering — dispatches the deep-research skill per category in Gap-Analysis/categories.md (completing that dispatch currently also requires the Workflow grant below), files well-scoped actionable gaps as GitHub issues, and writes broad/comparative findings into a dated Gap-Analysis/<date>.md report only. Ends fully non-interactively (no confirmation of any kind) so it is safe to run unattended from a cron job, even though the Operator triggers it manually today.
version: 1.0.0
---

> Version 1.0.0

You are comparing this vault's own design against current, real, external prior art in agentic engineering — not a one-time literature read, but a recurring mechanism. This is not `/growth` (the Operator's own recurring engineering patterns from session history) and not `/insight` (Claude Code usage habits) — this command diffs *this vault's own design* against what's actually published and current outside it.

This command has memory of its own past output, the same way `/growth` does, and ends fully non-interactively: no `AskUserQuestion`, no blocking confirmation of any kind, anywhere in this flow. It must be safe to run unattended from a weekly cron job even though the Operator runs it by hand today.

## Kill criteria this skill must self-report against

These were pre-registered when this command was designed (issue #24) and are not optional — every run's report must compute and state the numbers each one needs, so any reader (the Operator, or a future run of this command) can check them at a glance without digging back through old reports:

1. **Cadence noise:** if the first month of weekly runs (or first 3 manual runs) produces zero new actionable findings *and* zero non-repeat big-review findings → kill weekly cadence, revert to manual-only. Step 6 must state "N new actionable findings this run" and "N non-repeat big-review findings this run" every run, so this is checkable across runs without re-reading every report.
2. **Classification collapse:** if any single run buckets *everything* as big-review with nothing actionable → kill auto-issue-filing, route all findings through the report only from then on. Step 6 must state the actionable-vs-big-review split every run and flag explicitly if the split is 0 actionable.
3. **Unattended issue-spam:** if a single run files more than 2 GitHub issues that turn out, on Operator review, to be low-value → kill auto-filing; require the report to propose issues for the Operator to file themselves instead. Step 6 must state exactly how many issues were filed this run, and by number, so this is checkable at a glance without counting `gh issue create` calls by hand.
4. **Stale/wrong citations:** if a spot-check ever catches the research citing something factually *wrong* (not merely outdated) about an external framework → kill reliance on deep-research's unverified synthesis for that category until it requires a live fetched source per claim. Every finding this command writes (report or issue) must carry a real citation (a URL or a specifically named, checkable source) for the spot-check to even be possible — never accept or forward a bare unsourced claim from deep-research.

## Step 1 — Read prior Gap-Analysis reports

List `Gap-Analysis/` in this vault. If it doesn't exist yet, create it and skip to Step 2 — this is a first run.

If prior `Gap-Analysis/<YYYY-MM-DD>.md` files exist, read all of them (most recent first). For each, note: the date, each finding's category and title, whether it was routed as an actionable issue (and the issue number) or a report-only big-review finding, how many times a given finding has recurred, and how many issues were filed that run. This is what Step 6's repeat/escalation tracking and the kill-criteria numbers above are computed from.

## Step 2 — Read and grow the categories list

Read `Gap-Analysis/categories.md`. This file is the living "what to check" state for this command — it is never hardcoded into this file itself, because the field of relevant prior art keeps changing after this command was written.

Dispatch `deep-research` via the `Skill` tool (`skill: "deep-research"`) with a standing question: "What's currently relevant prior art in agentic engineering — frameworks, papers, named patterns, or practices — that is not already in this list: [paste the current contents of `categories.md`]?" Then follow whatever invocation instructions it returns — as of this writing, that's a `Workflow` dispatch, but don't hardcode the exact call shape here; follow what `deep-research` itself specifies each time, so this file doesn't go stale if that mechanism changes. Append anything genuinely new to `Gap-Analysis/categories.md`, each with a one-line reason for why it was added, before doing the actual comparison in Step 4. Do not remove or edit existing entries — this step only grows the list.

## Step 3 — Read the current vault design

Read `Principles.md`, every file in `Templates/Agents/`, and every file in `Templates/Skills/` in full. This is what gets diffed against each category in Step 4 — you need the vault's actual current shape, not a memory of it from a prior run.

## Step 4 — Dispatch deep-research per category

For each category in `Gap-Analysis/categories.md` (including any just added in Step 2), dispatch `deep-research` via the `Skill` tool, then follow the invocation instructions it returns (currently a `Workflow` dispatch — see Step 2), to research the current state of the art for that category, and compare it directly against the specific vault files read in Step 3. For each comparison, require a concrete answer to: does this vault already do this, partially do it, or not do it at all — and if there's a real gap, what would closing it look like. Require deep-research to back every claim with a real, checkable citation (a URL or a specifically named source) — never accept or carry forward an unsourced claim, per kill criterion 4 above.

## Step 5 — Route each finding

For each gap found in Step 4, classify it into exactly one of two paths — this classification must stay genuinely distinct (see kill criterion 2), never collapse to one bucket by default:

- **Well-scoped, actionable, low-ambiguity** (a single named file, a single named change, no open design question): file it directly as a GitHub issue — `gh issue create` — same paper-trail convention `shape.md` STEP 1 already uses for new ideas: the finding as given, no editorializing beyond what's needed to make it actionable, plus the citation(s) backing it. Label it `type:prior-art` (create the label first with `gh label create type:prior-art --color "5319e7" --description "Gap found by /gap-analysis comparing this vault's design against external prior art"` if it doesn't exist yet) — see [[Templates/GitHub/labels#type:prior-art]] for what this label does and does not imply.
- **Broad, comparative, or genuinely ambiguous** (spans multiple files, is a design tradeoff, or has no single clear fix): write it into the dated report only (Step 6). Never auto-edit `Principles.md` directly. Only when a big-review finding is about to be flagged for the 3rd time (counting this run, per Step 1's recurrence tracking) and is still open, draft a proposed addition to `Principles.md` — the same third-strike gate `growth.md` STEP 4 uses, not on every big-review finding. Below the 3rd occurrence, present the finding normally with no proposed addition.

State the count of each bucket explicitly — this is what kill criteria 1-2 above are computed from.

## Step 6 — Write the report

Format as Markdown using this vault's Obsidian conventions from `CLAUDE.md` (callouts for evidence and citations, e.g. `> [!tip] Evidence`, `> [!warning] Repeat` for a finding that recurred from a prior run; wiki-links where a concept connects to something already in this vault). Every finding — actionable or big-review — appears in the report; an actionable finding's entry also states the issue number it was filed as.

The report must open with the kill-criteria numbers this run computed, stated plainly and in one place:

- Categories checked this run (and how many were newly added in Step 2)
- New actionable findings this run / non-repeat big-review findings this run (kill criterion 1)
- Actionable vs. big-review split, flagged explicitly if 0 actionable (kill criterion 2)
- GitHub issues filed this run, by number (kill criterion 3 — the Operator checks these against the ">2 low-value" bar on review; this run's job is just to make the count and the list visible)
- Confirmation that every finding below carries a real citation (kill criterion 4)

Any proposed `Principles.md` addition — only ever drafted for a big-review finding on its 3rd flagged occurrence, per Step 5's third-strike gate — goes in its own `## Proposed additions to Principles.md` section at the end, each as a ready-to-paste callout block plus one sentence on where in `Principles.md` it would go — never written directly.

Get today's date (`date +%Y-%m-%d`) and write to `Gap-Analysis/<YYYY-MM-DD>.md`.

Tell the user the file was saved, the categories checked, how many findings were new vs. repeat, how many issues were filed (with numbers/links), and restate the kill-criteria numbers plainly so they don't have to open the file to check them.

## Related

- [[Gap-Analysis/categories]] — the load-bearing "what to check" state this command reads and grows every run
- [[Templates/Skills/shape]] — the issue paper-trail convention this reuses for actionable findings
- [[Templates/GitHub/labels]] — canonical definition of `type:prior-art`, added there in this same change
- [[Principles#Ground new additions in something citable]] — the citation discipline this command enforces on deep-research's own output
- [[Timeline]]
