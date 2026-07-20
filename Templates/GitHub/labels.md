# GitHub Label Taxonomy

The canonical label vocabulary this pipeline's agents and skills read and write. Every file in [[Templates/Agents]] and [[Templates/Skills]] that sets or checks a label should reference this doc by name instead of re-describing the taxonomy — see [[Principles#Shared shapes need one definition, not one description per reader]].

> [!note] Grounded in established practice
> Colon-namespaced labels (`category:value`) are a widely-used GitHub convention, not invented here — it groups related labels visually and makes filtering exact (`issue list --label "severity:critical"` can't accidentally match `severity:high`). [CUSTOMIZE] one label color per category, distinct shades per value within it, if this project's tracker supports label colors.

## Workflow-stage labels

[CUSTOMIZE] — this project's own state-machine names. The reference shape every template below assumes:

| Stage | Meaning | Set by |
|---|---|---|
| `idea` (or CUSTOMIZE) | Raw, untriaged | issue creation |
| `shaping` (or CUSTOMIZE) | Kept at triage, brief written, not yet a full spec | [[Templates/Agents/triage]] |
| `ready-to-build` (or CUSTOMIZE) | Full spec written, Definition-of-Ready satisfied | [[Templates/Skills/spec]] |
| `in-progress` (or CUSTOMIZE) | Claimed by the implementation supervisor | [[Templates/Skills/implement]] |
| `in-review` (or CUSTOMIZE) | PR open | [[Templates/Skills/implement]] |
| `rejected` (or CUSTOMIZE) | Killed at triage | [[Templates/Agents/triage]] |

Exactly one workflow-stage label is set at a time — every template that advances an issue removes the prior stage label when it sets the next.

## `safe-surface:<yes|no>`

[CUSTOMIZE: this project's actual safety-surface definition] — see [[Principles#Safety surfaces need a bright line, not a judgment call]]. Set by [[Templates/Agents/triage]] and [[Templates/Agents/ops-check]] at issue-creation time; re-verified (never re-decided) by [[Templates/Skills/implement]] STEP 7c.

This is the one spelling. Not "the safety-surface label," not `safety-surface:`, not `safe_surface` — every template and every prompt referencing this label uses this exact string.

## `severity:<critical|high|medium|low>`

Set on bug/regression issues only — skip for pure feature requests. Set by [[Templates/Agents/triage]] (from the reporter's account) and [[Templates/Agents/ops-check]] (from log evidence — see its STEP 3 for the critical/high/medium/low criteria).

## `needs:decision`

Bare flag, no value — this issue has at least one open question only the Operator can resolve. Set by [[Templates/Agents/triage]], [[Templates/Skills/spec]] (on an abandoned session), and [[Templates/Agents/ops-check]]. Cleared by whoever resolves the question — not automatic.

## `type:ecosystem-fix`

Marks a tracking issue for a fix to the *pipeline's own tooling* (an agent/skill file, not product code) — see [[Templates/GitHub/issue-templates#Ecosystem-fix tracking issue]]. Deliberately carries no workflow-stage label, on purpose: it should never surface in the normal shaping/ready/in-progress queue that [[Templates/Skills/queue-scout]] and [[Templates/Skills/implement]] scan. [[Templates/Skills/cleanup]] is the only thing that periodically checks these haven't gone stale.

## `type:prior-art`

Marks an issue that originated from `/gap-analysis` comparing this vault's own design against external prior art, rather than an idea the Operator typed themselves — see [[.claude/commands/gap-analysis]] STEP 5. This is a provenance tag only, not a workflow-stage label: a `type:prior-art` issue otherwise flows through the normal queue exactly like any operator-typed idea, sitting unlabeled beyond this tag until someone runs `/shape` on it. Unlike `type:ecosystem-fix` (which never gets a workflow-stage label at all and is watched by [[Templates/Skills/cleanup]] for staleness), no dedicated staleness watch exists for this label yet — `gap-analysis` isn't on a live cron yet, so building one now would be speculative; add one later if filed issues start piling up unread once cron is live.

## Model-routing labels (optional)

[CUSTOMIZE] — if this project routes different issues to different models, name the label and its values here. Delete this section if the project doesn't route.

## Area/partition labels (optional, secondary signal only)

[CUSTOMIZE] — e.g. `agent:core-logic`. [[Templates/Skills/queue-scout]] already treats these as a secondary signal, not a primary one, since they may not be set consistently on every issue.

## Related

- [[Principles#Shared shapes need one definition, not one description per reader]]
- [[Templates/GitHub/issue-templates]]
- [[Templates/GitHub/comment-templates]]
- [[Templates/Agents/triage]]
- [[Templates/Skills/spec]]
- [[Templates/Skills/implement]]
- [[Templates/Agents/ops-check]]
