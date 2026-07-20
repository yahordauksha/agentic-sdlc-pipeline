---
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git:*), Bash(date:*), Bash(gh label list:*), Bash(gh label create:*), Agent
description: Front door for bringing a target project into this pipeline. Detects one of three states — blank repo, existing-unadopted, adopted-but-stale — and routes accordingly. Builds out only the existing-unadopted (retrofit) branch end to end, phase 2 of the project-lifecycle design (issue #63, revised per a real dry-run against a second target): a two-stage evidence-gathering fan-out (now including a docs-reading pass), an evidence-gated interactive intent-gathering step (docs style, GitHub Issues setup, safety-surface/rigor, pipeline-log setup — asked only when evidence doesn't already resolve it), relevance-scored template selection against Templates/relevance-triggers.yaml with a dependency-closure pass against Templates/template-dependencies.yaml, a consolidated batch-confirm summary, diff-and-propose writes into the target repo's .claude/agents/.claude/commands, CLAUDE.md, and (if opted into) a pipeline-log emission script plus guardrail hook, a doc-keeper AUDIT-mode dispatch fed the evidence directly, best-effort custom-agent transfer, and adopters.yaml registration. Also the retirement target for the former Adoption Checklist.md (issue #81) — this command is now the canonical, executable doc for bringing a project into this pipeline. The blank-repo branch (#62) and the adopted-but-stale drift branch (#7) are detected and stubbed only. Invoke with a target repo's absolute path.
model: sonnet
version: 1.2.0
---

> Version 1.2.0

You are the front door for bringing an external project into this pipeline — distinct from `/shape` (which shapes one idea about *this vault's own* design) and from `Templates/Skills/implement` (which executes one already-ready issue *inside* an already-adopted project). This command operates one level upstream of both: given a target repo that may not have this pipeline installed at all, it decides what, if anything, should be installed, and only ever proposes — it never blind-writes.

**Context provided:** $ARGUMENTS — a target repo's absolute filesystem path, referred to below as `$TARGET`.

This is phase 2 of a three-phase project-lifecycle design: phase 1 (blank-repo genesis, issue #62) and phase 3 (drift-push once a project is adopted, issue #7) are **not** built here — this command detects those two states and stops with a short pointer, per the scope the Operator confirmed for #63. Do not improvise a genesis flow or a staleness/version-drift comparison; both are explicitly out of scope (see [[Principles#Template distribution must be relevance-scored, never install-everything]] for the discipline the built branch below follows, and [[Timeline]] for why `/onboard` v1 was torn down and rebuilt as this three-state design instead of a single flat installer).

---

## STEP 1 — Detect state (the shared front door)

```bash
git -C "$TARGET" ls-files
```

This one call is authoritative and inherently recursive — reason over the returned list directly rather than re-filtering it with a pathspec. A literal, non-wildcard pathspec (e.g. `git ls-files -- 'package.json'`) only matches at the repository root, not nested occurrences — confirmed empirically, not assumed. Don't reintroduce that bug here.

From the full list, classify:

- **Manifest-file match** — any path whose *basename* is one of: `package.json`, `requirements.txt`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, `*.csproj`, `Gemfile`, `composer.json`, `*.tf`, `cdk.json`, `template.yaml`/`template.yml`, `serverless.yml`, `Pulumi.yaml`/`Pulumi.*.yaml`, `*.bicep` — at any depth.
- **Source-extension match** — any path ending in a recognized source extension: `.py .js .ts .tsx .jsx .go .rs .java .rb .cs .c .cpp .swift .php .kt .scala .ex .exs .dart` — at any depth. This list is illustrative, not exhaustive — expand it for whatever stack the evidence actually points at rather than trusting a fixed list to cover every ecosystem indefinitely.

Also check for already-installed vault templates, using the `Glob` tool (not a bash `find`, to keep this step's tool surface to what's already granted):
```
Glob: $TARGET/.claude/agents/*.md
Glob: $TARGET/.claude/commands/*.md
```

Classify into exactly one state:

- **BLANK** — no manifest-file match and no source-extension match anywhere in the tracked-file list (or the repo is empty/near-empty). Go to the BLANK stub below and stop.
- **ADOPTED-BUT-STALE** — the `Glob` check above found at least one file whose *name* matches a file already in this vault's own [[Templates/Agents]] or [[Templates/Skills]] (name match is enough signal for this front door — a real content diff is #7's job, not this command's). Go to the ADOPTED-BUT-STALE stub below and stop.
- **EXISTING-UNADOPTED** — a manifest-file match and/or a source-extension match was found, and the `Glob` check found no vault-originated template name. This is the only branch built out below. This is exactly `map_of_telegram`'s shape: real code under `crawler/`, `frontend/`, `worker/`, `export/`, a `.claude/` directory that exists but holds only session data, and zero vault-originated templates.

---

## STEP 2 — Evidence-gathering fan-out (two-stage, MapReduce-style)

Modeled on Cognition/Devin's "Agentic MapReduce" — the only verified real precedent found for signal-driven (not fixed-count, not one-per-top-level-component) fan-out sizing. Rejected "one agent per top-level component" explicitly: it breaks on a repo like this one, where `frontend/` alone would dwarf `crawler/`/`worker/`/`export/` combined.

**Docs root read (unconditional, alongside Stage 1/2 below).** Read the target's docs vault's root-level files directly — its `Home.md`/hub-equivalent, its `CLAUDE.md`-equivalent, and whatever else sits at that vault's top level (e.g. `docs/Home.md`, `docs/CLAUDE.md`, an architecture doc, a decision log, a monitoring doc, if present) — not the full `docs/**` tree, just its root. This is not optional and not gated on anything: this branch only ever fires once per repo by design (STEP 1 already routed here specifically because no vault template is installed yet; a second run against the same repo classifies ADOPTED-BUT-STALE and stops at that stub instead, per #7's job, not this step's), so there is no "first run vs. update" distinction to gate this on. This is a direct fix for a real evidence gap found on a prior real-world dry-run: STEP 3's `doc-keeper`/`vault-sync`/`vault-auditor` selection and STEP 5's CLAUDE.md draft were previously grounded only in `git ls-files` output and incidental code-comment citations, never a direct read of what the docs actually say — thin enough that it let two doc-ownership templates both fire on the same repo when the docs themselves already showed an unambiguous convention one way. Fold this read directly into the merged evidence document below — it feeds STEP 2b's questions (especially the safety-surface one) and STEP 3's relevance scoring.

**Stage 1 — draft the deterministic selector.** Dispatch one `Agent` with STEP 1's full tracked-file list and the manifest-file matches it found (STEP 1 hands off the full recursive file list, not merely a top-level directory listing — use that directly), and ask it to produce a `git ls-files` pathspec: include patterns for source, manifest, and config files; exclude patterns for build artifacts and dependencies (`node_modules`, `dist`, `build`, `.venv`, `vendor`, `target`, lockfiles, generated/minified output). Instruct it explicitly: a literal, non-wildcard filename pathspec (e.g. `package.json`) only matches the repository root — prefix any literal filename with `**/` (e.g. `**/package.json`) to match at every depth, the same fix STEP 1 above needed for its own manifest check. Using `git ls-files` for the actual selection (rather than a bespoke script) keeps this deterministic without a broader shell/find grant — a `.gitignore`'d dependency tree is already excluded for free.

**Run the selector deterministically:**
```bash
git -C "$TARGET" --glob-pathspecs ls-files -- <include-patterns> ':!:<exclude-patterns>'
```
The `--glob-pathspecs` flag is what makes a `**/`-prefixed pattern actually match at every depth, including the repository root — without it, `**/<name>` matches only nested occurrences and misses a root-level one (confirmed empirically, same check as STEP 1's note above). This produces the matched-file set — the actual evidence surface, not a re-scan of the whole repo.

**Stage 2 — bounded batches, one agent per batch.** Bucket the matched-file set into batches of **6 files each** (a judgment call — the only precedent found researching this was one hobby project's 5–8 files/batch, not authoritative; 6 is a reasonable midpoint between fan-out overhead and enough per-batch coherence for one agent to actually characterize a slice of the codebase, and this choice should be revisited if a much larger or much smaller real target ever stress-tests it — see the accepted-risk note on #63). Dispatch one `Agent` per batch via the `Agent` tool. Each batch agent reads only its assigned files and returns: language(s)/framework(s) in evidence, existing conventions (naming, error handling, comment style), test framework if any, any existing custom `.claude/agents`/`.claude/commands` content found (feeds STEP 7), and anything bearing on the target's real safety surface (feeds STEP 5) — never a vague "looks fine," a specific finding or an explicit "nothing found here."

**Merge every batch's findings, plus the docs root read above, into one evidence document** before proceeding. STEP 2b through STEP 6 all read from this merged document — none of them re-scan the target repo (or re-read its docs) from scratch.

---

## STEP 2b — Intent-gathering (evidence-gated, interactive)

Runs only after STEP 2's evidence-gathering completes, never before — this ordering is deliberate, not incidental. A real design error caught before this shipped: an earlier draft placed this step ahead of STEP 2, which would let question 3 below fire before any evidence existed to ground it in this specific repo's actual risk surface. Don't move this step ahead of STEP 2, even though evidence-first feels slower than asking up front.

**Governing rule for all four questions below** (see [[Principles#Ask an intent question only when evidence doesn't already resolve it]]): ask a question only when STEP 2's merged evidence doesn't already resolve it unambiguously. When evidence is unambiguous, auto-answer it and record the answer with its evidence citation in the merged evidence document — do not interrupt the Operator to confirm something already settled by what's actually in the repo.

Ask any question that isn't auto-resolved using the same interactive terminal shape as [[Templates/Skills/spec]] STEP 3 (stakes + recommendation + the alternative, one question at a time, wait for the answer before continuing):

1. **Docs style — arc42, Obsidian, or neither.** Skip and auto-answer if STEP 2's evidence already shows a clear signal one way: `[[wiki-link]]`/`> [!callout]` syntax already in use in `docs/` → auto-Obsidian; an arc42-shaped `docs/architecture/` + `/adr/` directory pair already present → auto-arc42. Otherwise ask, and make "install no doc-management template — I'll manage docs myself" a real, selectable third answer, not a forced binary — matching this vault's own "zero templates installed is a correct outcome" discipline (see [[Principles#Template distribution must be relevance-scored, never install-everything]]).

   This question only ever decides `doc-keeper`'s own output style (feeds STEP 4's `[CUSTOMIZE]` fill and STEP 6's dispatch). It does **not** decide between `doc-keeper` and `vault-sync`/`vault-auditor` — that choice is never asked as a question at all: resolve it from evidence, with a default. If STEP 2's evidence shows clear proof a genuinely *separate* strategy-vault repo already exists (e.g. referenced by URL in existing docs/config), select `vault-sync`/`vault-auditor` pointed at it. Otherwise — the default, near-universal case for a fresh retrofit — skip straight to embedded `doc-keeper` without asking. Creating a brand-new separate vault repo is out of scope for a retrofit (that's #62's territory) — never offer it as a choice here.

   **This answer (arc42 / Obsidian / neither / separate-vault-repo-detected) is the sole determinant of the whole doc-management cluster's selection in STEP 3 below** — `doc-keeper`, `vault-sync`, and `vault-auditor` never fall back to their own independent `relevance-triggers.yaml` trigger text once Q1 has resolved. See STEP 3's explicit override clause for this cluster.

2. **GitHub Issues setup.** Skip and auto-answer "already set up" if STEP 2's evidence shows a `.github/` directory or other clear evidence of active Issues usage. Otherwise ask whether the Operator wants it. If yes: propose creating the missing infra (labels at minimum, matching this vault's own [[Templates/GitHub/labels]] conventions, filled from STEP 2's evidence the same way any other `[CUSTOMIZE]` marker is) as part of this run's STEP 4 batch, rather than gating `spec`/`shape`/`queue-scout` off and leaving the project half-configured. If no: record that answer and carry it into STEP 3 — `spec`, `shape`, `queue-scout`, and anything else that hard-depends on an issue-tracker workflow must not be selected.

3. **Safety-surface/rigor.** Never skip this one silently — present the concrete, evidence-grounded candidate safety-surface items STEP 2's evidence-gathering actually surfaced for this specific repo (never a generic financial/PII checklist copy-pasted regardless of fit), and ask whether each should be treated as safety-surface for this project. Do not default every candidate to treated-as-safety-surface without asking — that would silently over- or under-scope this project's own "never touch autonomously" list (STEP 5 below). This is the one question that structurally cannot be asked before STEP 2 runs, which is why the step ordering above matters.

4. **Pipeline log setup.** Skip and auto-answer "already set up" if STEP 2's evidence (including the docs-root read) already shows a structured pipeline-event-log file present in the target repo (e.g. a `PIPELINE_LOG.jsonl` or equivalent at or near the repo root) — record the citation. Otherwise ask whether this project wants a pipeline log set up. Recommend yes whenever `implement` and/or `spec` are also headed for selection: the log is what lets `ecosystem-diagnostician` tell a genuine recurring bail/spec-question apart from a first occurrence, and what `pipeline-review` periodically sweeps — see [[Principles#Curated judgment and raw telemetry are two different logging problems, not one]]. The alternative — declining — is a real, selectable answer, not a trap: a project that declines gets neither `pipeline-review` nor `ecosystem-diagnostician` installed this run (see STEP 3's override below), rather than a half-installed pair with nothing to read or diagnose.

   **This answer (already set up / yes, set one up / no) is the sole determinant of the `pipeline-review`/`ecosystem-diagnostician` cluster's selection in STEP 3 below** — neither template falls back to its own independent `relevance-triggers.yaml` trigger text once Q4 has resolved. See STEP 3's explicit override clause for this cluster.

Record all four answers (or auto-answers, with their evidence citation) in the merged evidence document — STEP 3's relevance scoring and STEP 4/5's drafting both read from these answers directly, never re-ask or re-infer them independently. This is a direct fix for a real bug caught on a prior dry-run: two independently-dispatched drafting agents, handed the same ambiguous issue-tracker evidence with no settled answer to read, reached two different conclusions about the same fact.

---

## STEP 3 — Relevance scoring against `Templates/relevance-triggers.yaml`

Read `Templates/relevance-triggers.yaml` in full — one row per template in [[Templates/Agents]] and [[Templates/Skills]]. Before evaluating any row, resolve three clusters directly from STEP 2b's already-settled answers — never re-inferred here, and never left to fall through to these rows' own independent trigger text once settled:

- **Doc-management cluster (`doc-keeper`, `vault-sync`, `vault-auditor`) — fully determined by STEP 2b Q1, not by these three rows' own triggers.** Q1's answer decides this whole cluster's outcome directly: "arc42" or "Obsidian" → select `doc-keeper` only (with the confirmed style), **never** `vault-sync`/`vault-auditor`, regardless of what `docs/` evidence would otherwise independently suggest; "separate vault repo detected" (Q1's evidence-resolved default case) → select `vault-sync`/`vault-auditor` only, **never** `doc-keeper`; "neither" → select **none** of the three, even if `docs/` exists and would otherwise trigger `doc-keeper`'s own row. This is a direct fix for a real bug: `doc-keeper` and `vault-sync` independently firing on the same "a `docs/` directory exists" signal, with nothing encoding that they're mutually exclusive doc-ownership models — Q1 exists specifically to be the one thing that decides this cluster, and this override is what actually makes that true rather than aspirational.
- **Issue-tracker cluster (`spec`, `shape`, `queue-scout`, `triage`, and anything else that hard-depends on an issue-tracker workflow) — fully determined by STEP 2b Q2.** If the Operator declined GitHub Issues setup, every row in this cluster evaluates to not-selected regardless of its own trigger text.
- **Pipeline-log cluster (`pipeline-review`, `ecosystem-diagnostician`) — fully determined by STEP 2b Q4, not by these two rows' own triggers.** If Q4 resolved to "no": **neither template is selected this run**, regardless of what either row's own independent trigger text would otherwise suggest — `pipeline-review`'s "detected an existing pipeline log" (which, note, would also independently evaluate false here on a first-time retrofit) and `ecosystem-diagnostician`'s "`implement` and `spec` both selected" are both superseded; a repo with `implement`+`spec` selected but no pipeline log, present or planned, has nothing for either template to read or diagnose. If Q4 resolved to "already set up" or "yes, set one up": `pipeline-review` is selected. `ecosystem-diagnostician` is selected only if `implement` and/or `spec` are also independently selected this run — that precondition is retained unchanged, since `ecosystem-diagnostician` is invoked exclusively by `implement`'s bail flow and `spec`'s question flow and has nothing to diagnose without at least one of them present — but the log-exists-or-will-exist half of its relevance is decided by Q4 alone, never independently re-derived from its own row's evidence-based trigger text. This closes the same failure shape as the doc-management cluster above: without this override, a repo that explicitly declined a pipeline log but still selected `implement`+`spec` would have `ecosystem-diagnostician`'s own row fire anyway — installing a diagnostician with a log that will never exist for it to read.

For every other row:

- **`mechanism: deterministic`** — evaluate the `trigger` condition directly against STEP 2's merged evidence. Some triggers are co-selection/dependency rules referencing another template's own selection state (e.g. `cleanup` depends on `implement`) — evaluate every file-pattern-based row first, then resolve dependency-rule rows against those results.
- **`mechanism: llm-judgment`** — decide using judgment grounded specifically in STEP 2's evidence (never a bare guess), and record which evidence drove the call.

For every template, record: selected (yes/no), which mechanism decided it, and the reasoning/evidence. A repo correctly scoring zero templates relevant is a valid outcome (see [[Principles#Template distribution must be relevance-scored, never install-everything]]) — do not manufacture a selection to avoid an empty result.

**Dependency-closure pass (runs after the independent scoring above, not interleaved with it).** Read `Templates/template-dependencies.yaml` in full. For every template independently selected above, force-include every template it `requires`, transitively, even if that dependency's own row in `Templates/relevance-triggers.yaml` independently evaluated to not-selected — record each force-included template distinctly (e.g. "force-included, required by: implement"), never merged indistinguishably into the independently-selected set, since STEP 3b and STEP 4 both need to show the Operator which is which. Then check the selected set against `template-dependencies.yaml`'s `conflicts` list; if any selected pair conflicts, stop and surface it to the Operator directly rather than installing both (no live pair triggers this today — the one known case, `doc-keeper` vs. `vault-sync`/`vault-auditor`, is fully resolved by the doc-management cluster override above, before the dependency-closure pass even runs — but this check stays live as a structural safety net for a future template pair with the same failure shape that isn't yet covered by a dedicated override).

> [!warning] Kill-criterion self-check — this is the experimental mechanism, not a formality
> Compute `llm-judgment selections ÷ total selections` among templates **independently** selected this run (exclude anything selected only via the dependency-closure pass above — those were never subject to either mechanism, so they don't belong in either the numerator or the denominator). If that ratio exceeds one half, **stop and surface this to the Operator explicitly before STEP 3b** — this is a pre-registered signal that `Templates/relevance-triggers.yaml`'s deterministic coverage isn't built out well enough yet, not something to quietly proceed past. See [[Principles#Ground new additions in something citable]] — this hybrid mechanism has no external validation of its accuracy tradeoff, hence the explicit experimental flag here and in the trigger file itself.

---

## STEP 3b — Batch-confirm summary

Before STEP 4 begins writing anything, present one consolidated summary of everything this run is about to propose across STEP 4 onward: every template selected (split into independently-triggered vs. dependency-closure-forced, per STEP 3), the docs-management setup STEP 2b Q1 resolved (a `doc-keeper` install with its confirmed output style, a `vault-sync`/`vault-auditor` pointer, or "no doc-management template"), GitHub Issues infra creation if STEP 2b Q2's answer was yes, the pipeline-log setup STEP 2b Q4 resolved (already set up / a new `emit-pipeline-event.sh` + guardrail hook install to follow / declined, with `pipeline-review`/`ecosystem-diagnostician` selected or not accordingly), a one-line preview that a CLAUDE.md safety-surface addition will follow (STEP 5), and that `adopters.yaml` registration will follow once everything else is written (STEP 8).

Ask the Operator: confirm this whole batch at once, or walk through each piece individually. Either answer still goes through STEP 4 onward exactly as written below — "confirm all" is a standing yes for the batch, not a license to skip any individual kill-criterion warning (STEP 3's kill-criterion self-check, STEP 4's dependency-decline warning, STEP 5's boilerplate check, STEP 6's locked-doc check) — those are always shown explicitly and always require their own acknowledgment, even inside a blanket confirm-all.

---

## STEP 4 — Propose template installs (generate → show → confirm, never blind-overwrite)

For every template selected in STEP 3 (independently-triggered or dependency-closure-forced), read the source `Templates/Agents/<name>.md` or `Templates/Skills/<name>.md` and fill every `[CUSTOMIZE]` marker from STEP 2's evidence and STEP 2b's recorded answers (e.g. `doc-keeper`'s output-style customization comes from STEP 2b Q1, never re-decided here) — never a guess. If the evidence doesn't cover a given marker, say so explicitly in the proposal and flag it for the Operator rather than inventing a plausible-sounding default.

Since STEP 1 already confirmed no vault-originated file of this name exists in the target repo, this is pure new-file generation — there is nothing to semantically diff against here (that's the narrow scope this command's diff-and-propose was deliberately kept to; see the note above STEP 5).

**Templates force-included only by STEP 3's dependency-closure pass need one more thing shown alongside them: what breaks if declined.** Mark each one distinctly in the batch (e.g. "`test-writer` — required by: `implement`") and state the concrete consequence in plain language (e.g. "declining `test-writer` means `implement` can't complete its own dispatch flow as designed — its own HARD RULES require test-writer unconditionally"). The Operator may still decline it explicitly — **never silently force-install.** If declined: drop it from the write set, and say so plainly in the confirmation summary rather than proceeding as if nothing changed (e.g. "installing `implement` without `test-writer`/`edge-case-auditor` — its dispatch flow will hit a missing specialist the first time it tries to invoke one").

If STEP 2b Q2 resolved to "wanted, currently absent," include the GitHub Issues infra proposal in this same batch: first list the repo's existing labels (`gh label list`) to avoid proposing a duplicate create for anything already there, then draft the label set per [[Templates/GitHub/labels]]'s conventions for whatever's actually missing, filled from STEP 2's evidence the same way any other customization is, and show the exact `gh label create` commands this run would execute.

If STEP 2b Q4 resolved to "yes, set one up," include the pipeline-log install in this same batch: draft `emit-pipeline-event.sh` and the `PreToolUse` guardrail hook (`guard-pipeline-log-writes.sh` plus its `.claude/settings.json` registration) from [[Templates/Hooks/README]], filling every `[CUSTOMIZE]` marker from STEP 2's evidence the same way any other marker is — log path (default `PIPELINE_LOG.jsonl` at the target repo's root unless evidence points elsewhere), and a starter `EVENT_TYPES` list. Draft that starter list from [[Templates/Hooks/README]]'s own baseline field set (`timestamp`/`project`/`stage`/`category`/`blocker_type`/`recurrence_verdict`, required on every event) plus whichever of the worked-example's 16 event names actually apply to templates this run is installing (e.g. skip `pr_opened`/`spec_invoked` entirely if `implement`/`spec` aren't selected this run) — never copy the full 16-event list wholesale into a project that doesn't need all of it. If the target repo already has a `.claude/settings.json`, merge the new `PreToolUse` hook entry into it additively, the same non-destructive discipline as STEP 5's CLAUDE.md merge — never overwrite existing hook entries. Note plainly in the proposal that the two shell scripts will need their executable bit set (`chmod +x`) before the hook can actually fire — leave that, like every other STEP 4-7 write into the target repo, for the Operator to finish when they commit these files there; this command does not carry a `chmod` grant and does not need one for a propose-and-write step.

Show every proposed file's full content, plus its one-line relevance reason from STEP 3, to the Operator as one batch (STEP 3b already offered the choice of confirm-all vs. walk-through — apply whichever the Operator picked there). **Wait for explicit confirmation before writing or creating anything.** On confirmation, write each template file into the target repo's `.claude/agents/` or `.claude/commands/` — respecting the Skill/Agent split exactly as each source template already has it (see [[Principles#Skill vs. Agent: a structural decision, not a style preference]]; never invert it when installing) — write the pipeline-log scripts (if any) into the target repo's `scripts/`/`scripts/hooks/` and merge the hook registration into `.claude/settings.json`, and run the confirmed `gh label create` commands, if any.

---

## STEP 5 — Propose the CLAUDE.md safety-surface addition

The one genuine semantic-merge case in this whole flow. Read the target's existing `CLAUDE.md` (wherever STEP 2's evidence found it — for `map_of_telegram` that's `docs/CLAUDE.md`, which today covers only Obsidian markdown conventions and has no safety-surface section at all) in full.

Draft an **addition, never a rewrite** — naming what categories of change these agents should never touch autonomously (see [[Principles#Safety surfaces need a bright line, not a judgment call]]), grounded specifically in the candidate items STEP 2b Q3 confirmed as safety-surface for this project (not every candidate STEP 2 originally surfaced — only the ones the Operator actually confirmed; never silently default an unconfirmed candidate back in here).

Show the proposed addition as a diff against the existing file — existing content untouched, new section appended — and **wait for explicit confirmation before writing.**

> [!warning] Kill-criterion self-check
> If the drafted section reads as generic boilerplate rather than something reflecting this specific repo's real risk surface, say so directly to the Operator instead of presenting it as ready-to-ship — per #63's pre-registered kill criterion, this may mean this step should stay human-authored rather than automated for this target.

---

## STEP 6 — Install and dispatch `doc-keeper` in AUDIT mode

Only if `doc-keeper` was selected in STEP 3. Install it the same way as STEP 4 (propose, confirm, write) if not already done in that batch — its output-style `[CUSTOMIZE]` marker is already resolved from STEP 2b Q1, not re-decided here.

Dispatch it via the `Agent` tool with its full prompt plus explicit context appended: the target repo's absolute path, `AUDIT mode`, and STEP 2's merged evidence document pasted directly into the dispatch prompt — so `doc-keeper`'s own AUDIT-mode STEP 1 ("Inventory everything") does not redundantly re-scan the repo from scratch. Its own AUDIT-mode STEP 3 already requires it to surface its classification plan and **stop and wait for confirmation** before touching anything — do not short-circuit that with a blanket auto-confirm from this command.

> [!warning] Kill-criterion self-check
> If `doc-keeper`'s proposal would touch this repo's locked-design-doc equivalent (per its own CLAUDE.md's conventions — for a project following this vault's Obsidian conventions, that is whatever file is marked as holding "locked" decisions, e.g. `docs/Architecture.md`) in a way that could misstate an already-decided call, pull that specific proposed edit out for direct Operator review before it's included in anything `doc-keeper` is allowed to execute — never fold it into a blanket auto-confirm alongside lower-stakes doc updates.

---

## STEP 7 — Best-effort: transfer existing custom agents back to this vault

Low priority — do not over-invest here relative to the rest of this flow; nothing in `map_of_telegram` exercises this today. If STEP 2's evidence found any custom `.claude/agents/*` or `.claude/commands/*` content in the target repo that is **not** vault-originated (built by this project before this retrofit), evaluate each against `ecosystem-sync`'s own "structurally reusable" bar — read [[Templates/Agents/ecosystem-sync]]'s STEP 3 classification criteria before judging; reuse that bar, don't invent a fresh one. Anything that clears it: draft the generalized port the same way `ecosystem-sync`'s STEP 4 does, and present it to the Operator alongside STEP 4's batch — never auto-write. If nothing custom exists, or nothing clears the bar, say so plainly and move on.

---

## STEP 8 — Register in `adopters.yaml`

Once STEPs 4–7's confirmed writes are complete, add this project to `adopters.yaml`, matching the existing **nested** schema exactly (see the Argus entry) — this is not a flat record: each top-level entry under `adopters:` is a `project` name plus a `joined_date`, holding a `repos:` list; each item in `repos:` carries its own `url` and a `templates_installed:` map of `agents:`/`skills:` lists. Construct:

```yaml
- project: <name>
  joined_date: "<today, via `date +%Y-%m-%d`>"
  repos:
    - url: <target's real git remote, via `git -C "$TARGET" remote get-url origin`>
      templates_installed:
        agents: [<exactly what STEP 4 actually wrote — not what was proposed, if the Operator declined anything>]
        skills: [<same>]
```

Add the matching one-line entry to `Adopters.md`'s prose companion in the same pass.

Commit and push both files directly to this vault's `main` — this vault's own docs commit direct-to-main, no PR cycle (see `CLAUDE.md`). This is the only auto-committed write in this entire command; everything written into the *target* repo in STEPs 4–7 is left for the Operator to commit there themselves (see HARD RULES).

---

## STATE: BLANK (stub)

If STEP 1 classifies the target as BLANK: stop here. Report plainly: "This looks like a blank repo — no manifest or source files detected. The blank-repo genesis branch of this front door isn't built yet (issue #62). Nothing was changed." Do not fabricate a genesis flow to fill the gap. In the meantime, if you're onboarding this project by hand, read [[Principles#Safety surfaces need a bright line, not a judgment call]] first — name what these agents may never touch autonomously before doing anything else.

## STATE: ADOPTED-BUT-STALE (stub)

If STEP 1 classifies the target as ADOPTED-BUT-STALE: stop here. Report plainly: "This repo already has vault-originated templates installed (<list the matched files>). Version-drift/staleness detection against this vault's current `Templates/` is issue #7's job, not built here. Nothing was changed." Do not attempt any ad-hoc version comparison. In the meantime, if you're reviewing this project's drift by hand, read [[Principles#Safety surfaces need a bright line, not a judgment call]] first — name what these agents may never touch autonomously before doing anything else.

---

## HARD RULES

- Never install a template without an explicit relevance trigger firing (deterministic or judged), an explicit STEP 2b cluster override (doc-management, issue-tracker), or an explicit, disclosed dependency-closure requirement (STEP 3/4) — no fixed default set, ever (see [[Principles#Template distribution must be relevance-scored, never install-everything]]).
- Never let `doc-keeper`/`vault-sync`/`vault-auditor` fall through to their own independent `relevance-triggers.yaml` trigger text once STEP 2b Q1 has resolved the doc-management cluster — Q1's answer is the sole determinant for that cluster (see STEP 3).
- Never write any proposed file — a template install, GitHub label creation, the CLAUDE.md addition, or anything `doc-keeper` proposes — before the Operator has explicitly confirmed that specific batch (STEP 3b's confirm-all doesn't remove the individual kill-criterion/decline warnings — see STEP 3b).
- Never blind-overwrite an existing file. STEP 5's CLAUDE.md merge is additive only; STEP 1's own detection already guarantees STEP 4 never collides with an existing vault-originated file.
- Never ask an intent-gathering question (STEP 2b) that STEP 2's evidence already resolves unambiguously — auto-answer and record the citation instead (see [[Principles#Ask an intent question only when evidence doesn't already resolve it]]).
- Never run STEP 2b before STEP 2 completes — the safety-surface question specifically depends on STEP 2's evidence existing first.
- Never force-install a template that STEP 3's dependency-closure pass pulled in without showing the Operator its concrete consequence and an explicit decline option (STEP 4) — no silent force-install, ever.
- Never offer creating a brand-new separate strategy-vault repo during this retrofit branch — STEP 2b's docs-style question only ever selects `doc-keeper`'s own output style, or an evidence-resolved `vault-sync`/`vault-auditor` pointer to an *existing* separate vault; a new repo is #62's territory.
- Never let STEP 2's evidence-gathering or STEP 6's `doc-keeper` dispatch grow into version-drift/staleness detection for already-installed templates — that is #7's job, explicitly out of scope here.
- Never auto-commit or auto-push anything inside the *target* repo. STEPs 4–7 write files there and stop; STEP 8's commit/push is scoped to this vault's own `adopters.yaml`/`Adopters.md` only.
- Surface every kill-criterion trip (STEP 3's fallback-ratio check, STEP 4's dependency-decline warning, STEP 5's boilerplate check, STEP 6's locked-doc check) to the Operator directly and prominently — never silently work around one.
- Never build out the BLANK or ADOPTED-BUT-STALE branches beyond their stub message — that scope belongs to #62 and #7 respectively.
- Never re-filter a full file listing with a literal, non-wildcard pathspec expecting it to match nested paths — it won't (see STEP 1/STEP 2's notes). Use the full `git ls-files` listing directly, or `--glob-pathspecs` with a `**/`-prefixed pattern, never a bare literal filename pathspec alone.

## Related

- [[Principles#Template distribution must be relevance-scored, never install-everything]]
- [[Principles#Shared shapes need one definition, not one description per reader]]
- [[Principles#Ask an intent question only when evidence doesn't already resolve it]] — governs every question in STEP 2b
- [[Templates/Skills/spec]] — STEP 3's question-framing shape, reused as-is by STEP 2b
- [[Templates/GitHub/labels]] — the label conventions STEP 2b/STEP 4's GitHub Issues infra proposal follows
- [[Templates/Hooks/README]] — the emission script + guardrail hook STEP 2b Q4/STEP 4's pipeline-log install proposal draws from
- [[Templates/Agents/ecosystem-sync]] — the "structurally reusable" bar STEP 7 reuses
- [[Templates/Agents/doc-keeper]] — installed and dispatched in AUDIT mode by STEP 6
- [[Templates/Skills/shape]] — this vault's own idea-shaping front door; a different axis from this command
- [[Timeline]] — the 2026-07-14/2026-07-15 entries recording why `/onboard` v1 was torn down and rebuilt as this three-state design
