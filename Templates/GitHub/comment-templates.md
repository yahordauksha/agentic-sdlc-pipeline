# GitHub Comment Templates

The two comment shapes this pipeline's agents and skills post — referenced by name from [[Templates/Skills/implement]], [[Templates/Skills/pipeline-review]], and [[Templates/Agents/ecosystem-diagnostician]], but never previously written down anywhere as literal text; each file assumed one of the others had defined it. See [[Principles#Shared shapes need one definition, not one description per reader]].

> [!note] Grounded in Conventional Comments
> Format follows [Conventional Comments](https://conventionalcomments.org/)'s `label (decorations): subject` + discussion shape — an established convention for structured review/status comments, not invented here. The label and decoration vocabulary below (blocker types, stage/category) is this pipeline's own; the syntax is borrowed directly.

## Blocked comment

Posted by [[Templates/Skills/implement]] STEP 8.4 on any BAIL.

```
**blocked (<blocker_type>):** <one-line summary of what stopped this>

**What was found:** <specific — file names, line numbers, no vague summaries>

**What's needed to unblock:** <concrete — a spec correction, an Operator decision, a dependency that needs to actually exist>

**Suggested path forward:** <one line — e.g. "re-run /spec with this context" or "needs Operator sign-off on X">
```

`<blocker_type>` is this reference implementation's own vocabulary: `spec-incomplete`, `missing-dependency`, `spec-codebase-conflict`, `ci-failure` — see [[Templates/Skills/implement]] STEP 8 for where each is triggered. [CUSTOMIZE] extend this list if a project's pipeline defines its own blocker types (e.g. an iac-specialist's destructive-change bail).

## Recurring-pattern comment

Posted by [[Templates/Agents/ecosystem-diagnostician]]'s caller (the implementation supervisor, the spec skill, or [[Templates/Skills/pipeline-review]] in periodic-sweep mode) on every issue in a group ecosystem-diagnostician has judged **RECURRING** — never posted by ecosystem-diagnostician itself, which is read-only on the issue tracker and only drafts text for its caller to post.

```
**recurring (bail — <stage>/<blocker_type>):** <one-line — shared root cause, from ecosystem-diagnostician's diagnosis>

**Prior occurrence(s):** #<issue> (<date>), #<issue> (<date>), ...

**Tracking issue:** #<ecosystem-fix issue number>
```

or, for a recurring spec-question:

```
**recurring (spec-question — <category>):** <one-line — the stable default answer, from ecosystem-diagnostician's diagnosis>

**Prior occurrence(s):** #<issue> (<date>), #<issue> (<date>), ...

**Tracking issue:** #<ecosystem-fix issue number>
```

One instance of this comment per issue in the recurring group — not one comment listing every issue, so each issue's own history shows the flag in its own context. The tracking-issue number referenced is the one created (or found, if one already exists) per [[Templates/GitHub/issue-templates#Ecosystem-fix tracking issue]].

## Related

- [[Templates/GitHub/issue-templates]]
- [[Templates/GitHub/labels]]
- [[Templates/Skills/implement]]
- [[Templates/Agents/ecosystem-diagnostician]]
- [[Templates/Skills/pipeline-review]]
