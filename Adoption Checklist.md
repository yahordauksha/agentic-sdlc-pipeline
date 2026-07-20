# Adoption Checklist

Steps to bring this pipeline into a new project. Read [[Principles]] first — the checklist tells you *what* to do, Principles tells you *why*, and you'll need the why to make the customization calls below well.

## 1. Name this project's safety surface

> [!important]
> Before anything else: what categories of change should these agents **never** touch autonomously? (Financial calculations, auth/authz, secrets/IAM, PII, whatever this domain's equivalent is.) Write it down somewhere every template can reference — the project's own CLAUDE.md is the right place. See [[Principles#Safety surfaces need a bright line, not a judgment call]].

## 2. Decide your issue-tracker state machine

The reference implementation assumes GitHub Issues + labels (`stage:ready` → `stage:in-progress` → `stage:in-review` → `stage:done`, plus a `stage:shaping` bail-back state). If this project uses Jira, Linear, or something else, map your own states to the same shape: ready-to-build, claimed/in-progress, blocked-needs-human, in-review, done.

## 3. Copy and customize the templates

For each file in [[Templates/Agents]] and [[Templates/Skills]]:
1. Copy it into the target project's `.claude/agents/` or `.claude/commands/` (agents vs. skills — see [[Principles#Skill vs. Agent: a structural decision, not a style preference]] if unsure which one a given specialist should be)
2. Fill in every `[CUSTOMIZE]` marker — project name, domain-specific standing invariants, tool names (linter, test runner, issue-tracker CLI), any codebase-graph/search MCP tools available
3. Do **not** invert the Skill/Agent split when porting — if a template is a Skill here because it dispatches other agents, it must stay a Skill in the new project even if that project's convention leans toward agents

## 4. Copy the usage-analysis commands (no customization needed)

`.claude/commands/insight.md` and `.claude/commands/growth.md` aren't pipeline-specific — they read Claude Code's global `~/.claude/usage-data/` and write relative to wherever they're invoked, so they can be copied into any project's `.claude/commands/` as-is. `insight` archives the built-in `/insights` report with a personalized "Nice to Learn" section on Claude Code usage; `growth` mines your session history for recurring *engineering* patterns and recommends system-design/documentation disciplines, tracking its own past output so repeats become a signal instead of noise.

## 5. Verify the pipeline once end-to-end before trusting it

Run it on one low-stakes issue first. Confirm: the supervisor actually dispatches specialists (proves the Skill conversion worked), the edge-case-auditor actually derives its own list before reading code (proves it isn't just rubber-stamping), and a deliberately-introduced bail actually produces a structured, actionable comment (proves STEP 8 works before you need it under pressure).

## 6. Wire the reverse sync (optional, but this is what stops future drift)

Install `Templates/Agents/ecosystem-sync.md` into the new project too, customized to point at this vault's actual path, and add a dispatch step to the project's own `implement` skill (mirroring the reference implementation's STEP 7d) so a PR touching `.claude/agents/*`/`.claude/commands/*` automatically ports genuinely-reusable changes back here — no one has to remember to do it by hand. Skipping this is fine for a quick trial, but every day it's skipped is a day this vault can silently drift behind what the project's pipeline actually looks like — which is exactly the failure this checklist's own templates existed in before this mechanism was built (see [[Timeline]]).

## Related

- [[Principles]]
- [[Templates/Agents/ecosystem-sync]]
- [[Home]]
