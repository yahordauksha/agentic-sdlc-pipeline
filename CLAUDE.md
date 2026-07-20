# Agent Ecosystem — Vault Instructions for Claude

This is the canonical reference for every agent and skill in this pipeline — the bible, not a snapshot. It is a documentation + template vault, not a code repo. It stores the reusable design of a multi-agent implementation pipeline (supervisor skill + specialist agents), the principles that pipeline was shaped by, and this vault's own skills for moving work between here and any adopting project.

The relationship with an adopting project is two-way, and both directions are this vault's job to keep working:
- **Vault → project:** `.claude/commands/project-lifecycle.md` now automates this direction for the existing-unadopted state — a project with real code but no vault templates installed yet gets evidence-gathered and relevance-scored, confirm-before-write (issue #63). The blank-repo (new project, #62) and adopted-but-stale (drift on an already-adopted project, #7) states are detected but still stubbed — manual, walking `Adoption Checklist.md`, until those land. An earlier `/onboard` skill attempted this direction as a single flat installer and was removed for this three-state redesign; see `Timeline.md`.
- **Project → vault:** `ecosystem-sync`, once installed in a project per `Adoption Checklist.md`, is dispatched automatically by that project's own implementation supervisor whenever a PR touches its `.claude/agents/*`/`.claude/commands/*`, and ports back anything genuinely reusable — no manual "go update the vault" step required. This is what closes the loop that used to require a human to remember.

Don't confuse this vault's own `.claude/commands/` (skills that run *in this vault's own session* — `insight`, `growth`, `shape`) with `Templates/Skills/` (skill *templates* meant to be installed into some other project). Same file shape, different purpose.

## Markdown / Obsidian conventions

This vault is opened in Obsidian. All `.md` files follow these rules (same conventions as the argus-docs vault):

- Use `[[wiki-links]]` to cross-reference other files (file name without extension; path-relative for subdirectories, e.g. `[[Templates/Agents/edge-case-auditor]]`)
- Use Obsidian callout syntax instead of bold-label blockquotes:
  - `> [!note] Title` — neutral context or background
  - `> [!tip] Title` — a generalizable insight worth reusing
  - `> [!warning] Title` — a failure mode this design specifically guards against
  - `> [!important] Title` — a non-negotiable invariant
  - `> [!question] Title` — an open design question, not yet resolved
- Add a `## Related` section near the end linking to sibling docs where relevant

## Key files

- `Home.md` — vault hub; links to everything below
- `Principles.md` — the cross-cutting design rules distilled from real incidents across projects. Read this before adapting any template — it explains *why* the templates are shaped the way they are, not just *what* they do
- `Templates/Agents/` — generalized subagent definitions (`.claude/agents/*.md` shape), stripped of project-specific domain details and marked with `[CUSTOMIZE: ...]` placeholders
- `Templates/Skills/` — generalized skill/slash-command definitions (`.claude/commands/*.md` shape), same placeholder convention
- `Adoption Checklist.md` — step-by-step guide for dropping these templates into a new project
- `Adopters.md` / `adopters.yaml` — human-readable and machine-parseable registry of adopting projects and what's installed where
- `Timeline.md` — narrative log of when and why the pipeline changed shape

## When you hit a design question you can't answer

Don't guess. Add it to `Principles.md` under an "Open questions" note (callout: `> [!question]`), or if it's project-specific, leave it out of the templates entirely.

Once you *can* answer it: every new Principle or Template still needs to name what it's grounded in before it ships — see `Principles.md`'s "Ground new additions in something citable."

> [!note] Bar for porting a pattern here is "structurally reusable," not "proven twice"
> Every template currently in this vault was ported after being used on exactly one project (Argus) — see `Timeline.md`. The bar for porting is whether the pattern has a genuinely reusable *shape* once project specifics are stripped out (a `[CUSTOMIZE]` pass makes it usable elsewhere), not whether it's already been re-proven on a second project. Don't gate a port on "wait for project #2" — that's not how any template here actually got in.

## Provenance

The original templates here were extracted from the `product/argus` code repo's `.claude/agents/` and `.claude/commands/`. Argus remains one live instance of this pipeline (the most complete one so far), not a special case — its own `ecosystem-sync` agent now ports genuinely-reusable changes back here automatically, the same mechanism any other adopting project gets by following `Adoption Checklist.md`.
