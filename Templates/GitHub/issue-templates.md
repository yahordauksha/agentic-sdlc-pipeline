# GitHub Issue Templates

The issue-body shapes this pipeline's agents and skills write — consolidated from where they previously lived only as inline text inside each agent/skill file. See [[Principles#Shared shapes need one definition, not one description per reader]].

> [!note] Grounded in established practice, not invented here
> [GitHub's own issue-forms guidance](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms) argues for essential-fields-only templates — the four shapes below already followed that discipline before this consolidation, so nothing here is padded to look more thorough. The bug-report shape is adapted from the standard OSS Steps-to-Reproduce/Expected/Actual convention, with one deliberate deviation noted in place: these are log-detected anomalies, not manually reproduced bugs, so "steps to reproduce" doesn't apply and "log evidence" substitutes for it.

## Triage brief

Written by [[Templates/Agents/triage]] STEP 4, appended to the issue body (original idea text preserved above it) on a KEEP verdict.

```
---
## Triage brief

**Verdict:** Keep

**Problem being solved:**
[One sentence — what user pain or friction does this address?]

**Proposed solution (rough):**
[One or two sentences — what would we actually build?]

**Invariant check:**
- [Invariant 1 — CUSTOMIZE]: [Safe / Needs careful scoping — explain if the latter]
- [Invariant 2 — CUSTOMIZE]: [Safe / Watch for leaks — explain if the latter]

**Safety surface touched:**
[List any safety-surface categories touched, per this project's own list — or: None]

**Effort estimate:** [XS / S / M / L / XL]
[XS = hours, S = 1–2 days, M = 3–5 days, L = 1–2 weeks, XL = more than 2 weeks]

**Open questions:**
[List any genuine unknowns that need resolution before spec. Leave empty if none.]
```

## Full spec

Written by [[Templates/Skills/spec]] STEP 4, replacing the triage brief section in the issue body.

```markdown
---
## Spec

**Problem statement:**
[Clear description of what is broken or missing and why it matters to a user]

**Proposed solution:**
[Precise description of what will be built — specific enough that an implementation agent could start without asking anything]

**Design artifact** (only present when [[Templates/Skills/spec]] STEP 1c's judge-panel design-exploration mode ran):
[A Mermaid diagram plus an interface/data-model contract for the selected candidate design — self-contained, the implementation agent should not need to reconstruct it from "Decisions made during spec" prose below. Omit this field entirely for an ordinary spec that never triggered design exploration.]

**Acceptance criteria:**
- [ ] [Testable criterion 1 — describes observable behaviour, not implementation]
- [ ] [Testable criterion 2]
- [ ] [Add as many as needed — no vague criteria like "works correctly"]

**Edge cases and failure modes:**
| Scenario | Expected behaviour |
|----------|-------------------|
| [e.g. external session expires mid-flow] | [e.g. re-authenticate silently, retry once, surface error to user on second failure] |
| [e.g. identifier checksum fails] | [e.g. reject immediately with specific error code, do not proceed] |

**Out of scope (explicitly):**
- [List anything adjacent that might seem related but is NOT in this issue]

**Implementation notes:**
[Specific technical guidance for the implementation agent: which files to touch, which patterns to follow, which to avoid. Reference actual file paths where relevant.]

**Test plan:**
[What tests must be written: unit tests for X, integration test covering Y, edge case Z must have a test]

**Decisions made during spec:**
[List every agent-resolvable question decided here, with the decision and rationale — one line each. Where a real alternative approach was weighed and rejected (not just "the obvious option"), name it and why — a future reader should see what was considered, not just what was picked.]
```

## Bug report (ops-check)

Written by [[Templates/Agents/ops-check]] STEP 5 for each new production anomaly (anomaly mode only — cost-efficiency mode findings use this project's normal product-infra issue convention instead, never this shape).

```markdown
## Bug report — [error signature]

**Severity:** [critical / high / medium / low]
**Detected:** [timestamp UTC]
**Occurrences:** [N times in window]
**Component:** [which service(s)]
**Window:** [time window checked]

### What happened
**Expected behavior:** [What should have happened]
**Actual behavior:** [What actually happened — plain language, what the user would have experienced]

### Log evidence
```
[Most relevant 5-10 log lines — truncated if longer. Never include token values, credentials, or PII.]
```

### Affected users
[user id list if visible in logs, otherwise: "not determinable from logs"]

### Likely cause
[If determinable from the log context. "Needs investigation" if unclear.]

### Suggested fix direction
[If obvious from the logs. Leave blank if genuinely unknown.]

### Open questions for Operator
[Only if a product/risk decision is needed to resolve this. Leave blank if it's a clean technical fix.]
```

> [!note] Deliberate deviation from the standard bug-report shape
> The conventional OSS format includes "Steps to reproduce" — that doesn't apply here since these are log-detected anomalies, not manually reproduced bugs. "Log evidence" is this shape's substitute: it's the evidence a human needs to confirm the bug, the same role reproduction steps would normally play.

## Ecosystem-fix tracking issue

Opened by [[Templates/Skills/pipeline-review]] STEP 4 the first time a RECURRING verdict is confirmed for a given `stage`/`blocker_type` or `category` — never duplicated; every call site dedup-searches by title before creating one.

**Title** (exact convention — every dedup search depends on matching this precisely):
```
Recurring bail: <stage>/<blocker_type>
```
or, for a recurring spec-question:
```
Recurring spec question: <category>
```

**Labels:** `type:ecosystem-fix` only — deliberately no workflow-stage label (see [[Templates/GitHub/labels#type:ecosystem-fix]]).

**Body:**
```markdown
## Recurring pattern: <stage>/<blocker_type, or category>

**Diagnosed by:** ecosystem-diagnostician, <date>
**Prior occurrence(s):** #<issue> (<date>), #<issue> (<date>), ...

**Shared root cause:** [from ecosystem-diagnostician's diagnosis]

**Diagnosed locus:** [exact file + section/step, or "vault Decision Policy" for a spec-question]

**Drafted fix:**
[the actual proposed text/change from ecosystem-diagnostician's output]

**Status:** Awaiting Operator review
```

## Related

- [[Templates/GitHub/labels]]
- [[Templates/GitHub/comment-templates]]
- [[Templates/Agents/triage]]
- [[Templates/Skills/spec]]
- [[Templates/Agents/ops-check]]
- [[Templates/Skills/pipeline-review]]
- [[Templates/Agents/ecosystem-diagnostician]]
