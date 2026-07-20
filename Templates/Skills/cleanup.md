---
allowed-tools: Bash(git:*), Bash(<issue-tracker> issue:*), Bash(<issue-tracker> pr:*), Read, Grep, Glob
description: End-of-session workspace hygiene sweep. Removes worktrees/branches that are unambiguously safe (merged into main, or remote-deleted/[gone]) after one batch confirmation, reports anything ambiguous (dirty, unmerged, stale) without touching it, and surfaces orphaned in-progress issues, aging ecosystem-fix tracking issues, and stale draft PRs that nothing else watches. Invoke manually at the end of a coding session.
model: sonnet
version: 1.0.0
---

> Version 1.0.0

You are running an end-of-session hygiene sweep for **[CUSTOMIZE: project name]**. The goal is that the Operator can run this once before closing out and trust the workspace is clean — no orphaned worktrees, no dead branches, no silently-stuck issues — without collecting code debt across sessions.

**Context provided:** $ARGUMENTS (none needed — always sweeps the full worktree/branch/issue state)

**Scope:** this code repo only. Never touch a separate strategy/docs vault, if this project has one — that has its own repo and its own hygiene owned by `vault-auditor`.

---

## STEP 1 — Refresh remote state (mechanical)

```bash
git fetch --prune origin
git worktree prune -v
```

`--prune` on fetch updates remote-tracking refs so `[gone]` detection in STEP 3 is accurate instead of working off a stale view. `git worktree prune` clears git's own registry of any worktree directory that was deleted manually outside git (e.g. `rm -rf` instead of `git worktree remove`) — without this, `git worktree list` keeps reporting orphaned metadata.

---

## STEP 2 — Inventory

```bash
git worktree list --porcelain
git branch -vv
```

Build one entry per non-`main` branch (a branch may have a live worktree, or may be worktree-less — already merged and its worktree already removed, just the branch left behind). For each, gather:

- **Worktree path**, if any.
- **Dirty vs. clean** — `git -C <path> status --porcelain` (skip if no worktree; a worktree-less branch can't be dirty).
- **Gone-remote** — `git branch -vv` showing `: gone]`.
- **Merged into main** — `git merge-base --is-ancestor <branch> origin/main` (exit 0 = merged; don't rely on text-parsing `git branch --merged`, a squash-merge won't show up there even though the content landed).
- **Associated PR** — `<issue-tracker> pr list --head <branch> --state all --json number,state,isDraft,mergedAt`.
- **Last commit age** — `git log -1 --format=%cI <branch>`.

---

## STEP 3 — Classify

- **SAFE-MERGED** — clean (or worktree-less) AND (merged-into-main OR PR `state: MERGED`). Auto-remove eligible.
- **GONE** — `[gone]` remote marker AND clean (or worktree-less). Auto-remove eligible.
- **DIRTY** — uncommitted changes present. Never auto-touch. Report only; tell the Operator to commit/stash/discard it themselves first.
- **ACTIVE** — an open PR (draft or not) exists, OR last commit is within 48h. Leave alone, report status only.
- **STALE-UNMERGED** — clean, not merged, no open PR, last commit older than 7 days. Flag for individual confirmation — this could be intentionally paused work, never batch-delete it.

A branch can match more than one signal (e.g. `[gone]` but also dirty) — dirty always wins the classification; never auto-remove anything with uncommitted changes regardless of its remote/merge state.

---

## STEP 4 — Execute safe removals (one batch, one confirmation)

List every SAFE-MERGED and GONE item together and ask the Operator to confirm the whole batch once — not per item; per-item confirmation is exactly the friction that makes people skip cleanup. On confirmation:

```bash
git worktree remove <path>   # never --force
git branch -d <branch>       # never -D
```

`-d`/no `--force` are deliberate: git's own refusal-to-delete-unmerged and refusal-to-remove-dirty checks are a second, independent safety net on top of this skill's own classification. If `git branch -d` refuses despite our merge-base check saying merged (e.g. a divergent base), stop, do not force it, and report the discrepancy instead of overriding git's judgment.

If the Operator declines the batch, or wants to exclude specific items, skip exactly those and proceed with the rest.

---

## STEP 5 — Issue-tracker cross-checks

**a. Orphaned in-progress issues.** `<issue-tracker> issue list --label "<in-progress label>" --json number,title,updatedAt`. For each, check whether any open PR references it and check the pipeline log (if this project has one) for the most recent line mentioning that issue number. No open PR and no recent log activity (>3 days) → **ORPHANED CLAIM**: the issue is marked in-progress but nothing is actually moving it. Report it; don't relabel it yourself — that's an Operator or implementation-supervisor call.

**b. Aging ecosystem-fix issues.** `<issue-tracker> issue list --label "type:ecosystem-fix" --state open --json number,title,createdAt`. [CUSTOMIZE] These deliberately carry no normal workflow-stage label specifically so the queue scout / implementation supervisor never surface them — which also means nothing else in the pipeline ever reminds the Operator they're waiting. Flag any open longer than 30 days with their age.

**c. Stale draft PRs.** `<issue-tracker> pr list --state open --json number,title,isDraft,updatedAt`, filtered to `isDraft: true` and not updated in 14+ days. A draft is drafted specifically because it needs a human merge decision — a stale one means that decision has been sitting unmade.

---

## STEP 6 — Report

Terminal report only, same shape as `queue-scout`/`pipeline-review`.

```
CLEANUP SWEEP — <N> branches/worktrees checked

✅ SAFE-MERGED — removed after confirmation:
  <branch>   [PR #<n> MERGED, worktree clean]  → worktree + branch removed

🗑 GONE — removed after confirmation:
  <branch>   [remote deleted, no worktree] → branch removed

⚠️ DIRTY — left untouched, needs your attention:
  <branch>   [uncommitted changes] — commit, stash, or discard before this can be cleaned

⏳ STALE-UNMERGED — needs individual confirmation, not auto-deleted:
  <branch>   [no PR, last commit <date>, <N> days ago] — still wanted, or safe to drop?

🟢 ACTIVE — left alone:
  <branch>   [open PR #<n>]

❓ ORPHANED CLAIM — in-progress, no visible activity:
  #<issue> <title>   [last log activity <date>, no open PR]

🕰 AGING ECOSYSTEM-FIX — open >30 days, nothing else will surface these:
  #<issue> <title>   [opened <date>]

📝 STALE DRAFT PR — open, no update in 14+ days:
  #<pr> <title>   [updated <date>]

Recommended next action: <e.g. "nothing else needs attention" or "decide on the 2 stale-unmerged branches before next session">
```

If a category is empty, omit it — don't pad the report to look thorough.

---

## HARD RULES

- Never `git worktree remove --force` or `git branch -D` — rely on git's own dirty/unmerged refusal as an independent second check on top of this skill's classification, never override it.
- Never auto-delete anything classified DIRTY or STALE-UNMERGED — those always require explicit per-item confirmation, batch auto-delete applies only to SAFE-MERGED/GONE.
- Never touch `main`'s own worktree or branch.
- Never edit issue labels, comment on issues, or relabel an ORPHANED CLAIM — report it and let the Operator or implementation supervisor decide; this skill's only write action is worktree/branch removal, and only after explicit batch confirmation.
- Never touch a separate strategy/docs vault repo, if this project has one.

## Related

- [[Principles]]
- [[Templates/Skills/queue-scout]]
- [[Templates/Skills/pipeline-review]]
- [[Templates/Agents/vault-auditor]] — owns hygiene for the separate vault, if one exists, that this skill deliberately never touches
