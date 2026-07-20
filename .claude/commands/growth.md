---
allowed-tools: Bash(ls:*), Bash(date:*), Read, Write
description: Analyze your full Claude Code session history for recurring engineering patterns and recommend system design, architecture, and documentation practices to learn from them — tracking what was already flagged so repeats become a signal, not noise.
version: 1.0.0
---

> Version 1.0.0

You are analyzing the user's Claude Code session history to find recurring *engineering* patterns — not Claude Code usage tips (that's `/insight`'s job) — and recommending real software-engineering, system-design, or documentation disciplines that would make them a better engineer. This runs on-demand only; there is no dependency on the built-in `/insights` report.

This command has memory of its own past output. The point isn't to hand back a fresh-looking list every time — it's to notice whether a past finding got acted on, and say so plainly.

## Step 1 — Read prior Growth reports

List `Growth/` in this vault. If it doesn't exist yet, create it and skip to Step 2 — this is a first run.

If prior `Growth/<YYYY-MM-DD>.md` files exist, read all of them (most recent first). For each, note: the date, each recommendation's title, the specific evidence cited for it (session IDs/counts), how many times it's already been flagged (a repeat block says so explicitly — carry that count forward), and whether it carries a `> [!success] Applied` marker underneath it.

A `> [!success] Applied` marker means the user has manually noted they read/applied that finding's resource. Treat it as an acknowledgment, not a resolution — still check the new evidence in Step 4. If the pattern still shows up in sessions *after* the marker's report date, that's a stronger finding than an ordinary repeat: the resource was tried and the failure mode persisted anyway, which points at a structural fix, not more reading.

Also note how long it's been since the most recent prior report. If it's been less than ~2 weeks, say so plainly to the user later — there likely hasn't been enough new work for the underlying patterns to have shifted, and that itself is worth naming rather than papering over with a reworded list.

## Step 2 — Read all available facet data

Read every JSON file in `~/.claude/usage-data/facets/` — all of it, however far back it goes. Do not filter by date or sample; the whole directory is the data window ("as long as possible" is the point).

Each file has: `underlying_goal`, `goal_categories`, `outcome`, `friction_counts`, `friction_detail`, `primary_success`, `brief_summary`.

## Step 3 — Mine for engineering signal, not just categories

The category counts (`goal_categories`, `friction_counts`) tell you *what* the user did. The free-text fields — `underlying_goal`, `brief_summary`, `friction_detail` — tell you what actually went wrong or right at a technical level (e.g. a fix silently breaking a different acceptance criterion, a multi-stage pipeline losing state on failure, docs drifting from shipped code, a spec catching a conflict before it was built). Read across ALL sessions' free text before drafting anything — the categories alone are not enough signal.

Look for patterns that map to a *named, learnable discipline*: architectural patterns (e.g. saga/orchestration patterns, contract testing between pipeline stages, idempotency, event-driven design), documentation frameworks (e.g. Diataxis, ADR formats), or general system-design fundamentals (e.g. consistency/failure modes, dependency graphs, versioning strategies). Only surface a pattern if it recurs — a single one-off incident is not a pattern.

## Step 4 — Reconcile against prior reports

For each candidate finding from Step 3, check it against the titles/themes read in Step 1:

- **New pattern** (wasn't flagged before, or the prior report predates the sessions that now establish it): present normally.
- **Repeat pattern** (substantially the same discipline/gap flagged in a prior report): do not silently restate it as if fresh. Instead:
  - Say explicitly this is a repeat and how many times it's now been flagged (with the dates).
  - Check whether the NEW evidence (sessions since the last report) still shows the same failure mode, or whether it's actually stopped appearing — if it's stopped, say so and retire it instead of re-listing it.
  - If it's still happening and was never marked `Applied`: say so plainly and ask directly whether the recommended resource was actually read/applied, rather than restating the resource as if it's new advice.
  - If it's still happening and WAS marked `Applied` in a prior report: say so explicitly — the resource was tried and the pattern persisted anyway. This is escalated signal, not an ordinary repeat.
- **Third-strike escalation**: if a pattern is about to be flagged for the 3rd time (counting this run) and is still open, do not just flag it again. Instead, draft a proposed addition or sharpening to `Principles.md` that would make the failure mode structurally harder to hit — the same shape as the existing entries there (a named rule, a `[!warning]`/`[!important]` callout, a one-paragraph account of why). Present the draft to the user as a proposal at the end of the report; do not edit `Principles.md` yourself. This is the same "close the loop" move as recurring friction elsewhere — three appearances means reading assignments aren't the fix.

A report with zero new patterns and one or two "still open" repeats is a valid, useful output — do not manufacture new findings just to fill space.

## Step 5 — Write the recommendations

Each finding (new or repeat) must:

- Name the specific recurring pattern, citing actual counts/examples from the session data (e.g. "3 of your last N sessions had a pipeline stage's fix silently break a different downstream guarantee").
- Name the underlying engineering discipline or architecture concept it points to.
- Recommend one or two specific, real, well-established resources — books, canonical papers/articles, or well-known named frameworks/patterns. Never invent or guess a URL, book title, or author you aren't confident is real. Do NOT recommend Claude Code features/docs here — that is out of scope for this command.

Do not include filler ("learn more about X") that isn't tied to an observed pattern in the data. Cap total findings (new + repeat) at 6.

## Step 6 — Save and confirm

Format as Markdown using this vault's Obsidian conventions from `CLAUDE.md` (callouts for evidence, e.g. `> [!tip] Evidence`; a distinct callout style like `> [!warning] Repeat (Nth time)` for repeats so they're visually distinct from new findings; wiki-links where a concept connects to something already in this vault). Any third-strike escalation goes in its own `## Proposed additions to Principles.md` section at the end, each as a ready-to-paste callout block plus one sentence on where in `Principles.md` it would go.

Below each finding that's still open, add a one-line note telling the user how to close it out: `_Mark this Applied once you've read/tried the resource above, by adding "> [!success] Applied" directly below this line._`

Get today's date (`date +%Y-%m-%d`) and write to `Growth/<YYYY-MM-DD>.md` in this vault.

Tell the user the file was saved, state the data window covered (date range + session count), how many findings were new vs. repeats vs. third-strike escalations, and if it's been under 2 weeks since the last report, say that plainly too.
