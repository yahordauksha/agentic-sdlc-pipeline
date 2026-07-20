# CI Workflow Template

The one CI/CD workflow this pipeline's templates actually assume exists — grounded directly in what's referenced elsewhere, not speculative. See [[Principles#Shared shapes need one definition, not one description per reader]] for the general discipline this follows.

> [!note] Scoped narrower than a full CI/CD suite, on purpose
> Ideas.md originally framed this as templating six workflows (`ci`, `deploy`, `pr-review`, `issue-triage`, `auto-merge`, `auto-rebase`) — re-checking the actual templates found that premise didn't hold. None of the other five are assumed anywhere in this vault's own files. The one real, grounded dependency is [[Templates/Skills/implement]] STEP 7c's self-review step ("linter, test suite") — an adopting project needs a CI workflow that runs the same checks automatically on every PR, or that step is trusting a check that only ever runs when an agent remembers to run it locally. [[Templates/Skills/pipeline-review]] STEP 4b (CI volume/cost trend) also assumes *some* CI workflow exists to pull run data from — this is that workflow. `deploy`/`auto-merge`/`auto-rebase`/`pr-review`/`issue-triage` automation aren't templated because nothing currently in this vault's templates actually depends on them existing — building them now would be seeding speculative capability, not closing a real gap. Revisit if a future template actually starts assuming one of them.

## `ci.yml`

Runs on every PR and every push to main. [CUSTOMIZE] every step to this project's actual language and tooling — the shape (lint, test, and an optional architecture-boundary check) is what matters, not the specific commands shown.

The lint and test commands here must be the *same* commands [[Templates/Skills/implement]] STEP 7c runs locally before opening a PR — this workflow is what makes that check enforced automatically on every PR, instead of only ever running when a supervisor session remembers to run it.

## Related

- [[Templates/Skills/implement]] — STEP 7c is what this workflow automates
- [[Templates/Skills/pipeline-review]] — STEP 4b reads this workflow's run history
- [[Principles#Shared shapes need one definition, not one description per reader]]
