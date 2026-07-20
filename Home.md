# Agent Ecosystem

The canonical reference for every agent and skill in this multi-project pipeline — the bible, not a snapshot. It stores the generalized templates (a supervisor skill that claims a piece of work and dispatches specialist agents — implement, test, adversarially audit, check infra, keep docs in sync — through to a reviewed PR), the [[Principles]] those templates were shaped by, and its own skills for moving work between here and any adopting project.

The relationship with every project that adopts this pipeline is **two-way**, not adopt-once-and-drift:
- **Vault → project:** `.claude/commands/project-lifecycle.md` now automates this direction for the existing-unadopted state — a project with real code but no vault templates installed yet gets evidence-gathered and relevance-scored, confirm-before-write (issue #63). The blank-repo (new project, #62) and adopted-but-stale (drift on an already-adopted project, #7) states are detected but still stubbed — manual, walking [[Adoption Checklist]], until those land. An earlier `/onboard` skill attempted this direction as a single flat installer and was removed for this three-state redesign; see [[Timeline]].
- **Project → vault:** `ecosystem-sync` (installed in the target project per [[Adoption Checklist]]) watches that project's own `.claude/agents/`/`.claude/commands/`, and automatically ports back anything genuinely reusable it builds or sharpens — dispatched by that project's own implementation supervisor on every PR that touches pipeline tooling, no manual "go update the vault" step required.

> [!note] Provenance
> Originally extracted from the `product/argus` code repo. Argus remains one live instance of this pipeline (currently the most complete one), not a special case — any project that adopts the templates and wires up `ecosystem-sync` is on equal footing going forward. See [[CLAUDE]] for how a specific project repo and this vault relate.

## Start here

- [[Principles]] — the *why* behind every template. Read this first.
- [[Adoption Checklist]] — the step-by-step guide for bringing this pipeline into a new project. Currently manual; see [[Timeline]] for why the automated `/onboard` skill was removed.
- [[Adopters]] — which projects have adopted this pipeline so far and what's installed where; `adopters.yaml` is the machine-parseable counterpart.
- Ideas.md — retired and removed; this vault's backlog now lives as GitHub issues on this repo, fed by `/shape` (see below) rather than a markdown dump.

## Templates

**Skills** (dispatch-capable — run inline in the main session):
- [[Templates/Skills/shape]] — interactive front door for one idea at a time: ICE/RICE score, a real pre-mortem, pre-registered kill criteria, then a handoff into `/spec` and beyond
- [[Templates/Skills/implement]] — the supervisor: claims work, dispatches specialists, opens the PR
- [[Templates/Skills/queue-scout]] — read-only dependency- and feasibility-verification scout across the whole queue
- [[Templates/Skills/spec]] — interactive spec-writer that turns a rough issue into implementation-ready; also the one place this ecosystem drafts an ADR
- [[Templates/Skills/cleanup]] — end-of-session worktree/branch/issue hygiene sweep
- [[Templates/Skills/pipeline-review]] — periodic broad sweep over the pipeline's own event log: recurring-pattern catch-up, decision-outcome correlation, token/CI/cloud resource efficiency

**Agents** (isolated context — do one job, return a result):
- [[Templates/Agents/edge-case-auditor]] — independent adversarial audit, the richest pattern in the ecosystem
- [[Templates/Agents/core-implementer]] — writes the feature code
- [[Templates/Agents/test-writer]] — writes the tests
- [[Templates/Agents/doc-keeper]] — keeps documentation in sync (arc42 + Nygard ADRs + C4), incremental or audit mode
- [[Templates/Agents/iac-specialist]] — infrastructure-as-code changes, read-only plan only
- [[Templates/Agents/triage]] — evaluates and labels incoming raw ideas
- [[Templates/Agents/ecosystem-diagnostician]] — judges whether a recurring bail/spec-question is a genuine repeat, and drafts a fix
- [[Templates/Agents/ops-check]] — production log anomaly sweep, plus a cloud cost/right-sizing mode
- [[Templates/Agents/vault-sync]] — auto-syncs a separate product-strategy vault from code-repo changes
- [[Templates/Agents/vault-auditor]] — periodic broad consistency sweep of that same strategy vault
- [[Templates/Agents/ecosystem-sync]] — the agent that keeps *this* vault's own `Templates/` in sync with a source project, the mechanism behind the vault→project relationship described above
- [[Templates/Agents/prompt-implementer]] — edits agent/skill *definition* files rather than product code, tiered by reversibility, never grading its own medium/high-tier work
- [[Templates/Agents/prompt-auditor]] — its independent audit, dispatched twice (independently) for HIGH-tier edits
- [[Templates/Agents/design-critic]] — independent adversarial review of one candidate architectural design, dispatched once per candidate by `/spec`'s STEP 1c judge-panel design-exploration mode

**GitHub interaction layer** (not agents/skills — the canonical shared shapes the templates above read and reference instead of each re-describing):
- [[Templates/GitHub/labels]] — the label taxonomy
- [[Templates/GitHub/issue-templates]] — triage brief, full spec, bug report, ecosystem-fix tracking issue
- [[Templates/GitHub/comment-templates]] — the blocked comment and recurring-pattern comment

**CI** — [[Templates/CI/README]] — the one workflow (`ci.yml`: lint + test) this pipeline's templates actually assume exists, grounded in `implement.md` STEP 7c and `pipeline-review.md` STEP 4b rather than speculative

**Hooks** — [[Templates/Hooks/README]] — sanctioned emission script + `PreToolUse` guardrail hook for a curated pipeline event log, grounded in the already-shipped `worktree_violation_caught` hook and read by `pipeline-review.md`'s own write-mechanism note

See [[Timeline]] for the porting history, including the drift this vault found in itself before this pass (four agents and two skills had existed in Argus with no Templates counterpart at all).

## This vault's own skills

Unlike the pipeline templates above, these run directly in this vault's own session — no `[CUSTOMIZE]` markers, nothing to install elsewhere.

- `.claude/commands/insight.md` — archives the built-in `/insights` report into `Insights/`, with a personalized "Nice to Learn" section on Claude Code usage grounded in real session data. Drop-in, copy as-is into any project.
- `.claude/commands/growth.md` — mines session history for recurring *engineering* patterns (not Claude Code usage tips) and recommends system-design/architecture/documentation disciplines, saved to `Growth/`. Reads its own past output first, so a repeated finding is flagged as a repeat rather than silently re-listed. Drop-in, copy as-is into any project.
- `.claude/commands/shape.md` + `.claude/agents/prompt-implementer.md` + `.claude/agents/prompt-auditor.md` — live, customized copies of [[Templates/Skills/shape]]/[[Templates/Agents/prompt-implementer]]/[[Templates/Agents/prompt-auditor]], wired to this vault's own GitHub issues instead of a generic issue-tracker placeholder. This is how a new idea about this vault's own design actually gets shaped and implemented, from here, going forward.
- `.claude/commands/project-lifecycle.md` — front door for bringing a target project into this pipeline: detects blank / existing-unadopted / adopted-but-stale state and routes accordingly. Only the existing-unadopted (retrofit) branch is built out (issue #63) — evidence-gathers via a two-stage MapReduce-style fan-out, relevance-scores template selection against `Templates/relevance-triggers.yaml`, and never installs anything without explicit confirmation. The other two states are detected and stubbed, pointing to #62/#7.
- `.claude/commands/gap-analysis.md` — periodic sweep comparing this vault's own design (`Principles.md`, `Templates/Agents/*.md`, `Templates/Skills/*.md`) against current external prior art, dispatching `deep-research` once per category in [[Gap-Analysis/categories]] (the "what to check" list it grows each run). Files well-scoped gaps as GitHub issues; broader findings go to a dated `Gap-Analysis/<date>.md` report. Each `deep-research` dispatch fans out into dozens of subagents — weigh that cost before running it broadly.
- `scripts/lint_vault.py` + `.github/workflows/vault-lint.yml` — this vault's own structural lint, not a template: every `[[wiki-link]]` must resolve to a real file/header, every `Templates/Agents`/`Templates/Skills` file must have its required frontmatter fields. Runs on every PR to this repo.

## Log

- [[Timeline]] — when and why the pipeline changed shape
- `Insights/` — raw HTML reports from Claude Code's `/insights` command, dated (`YYYY-MM-DD.html`), so usage patterns and friction points are visible over time instead of overwritten each run
- `Growth/` — dated Markdown reports from `/growth`, same append-only convention
- `Gap-Analysis/` — dated Markdown reports from `/gap-analysis`, comparing this vault's own design against external prior art; same append-only convention. [[Gap-Analysis/categories]] is the living "what to check" list it reads and grows each run.

## Related

- argus-docs vault (product-specific planning) — separate vault, not linked here since it's a different Obsidian vault
