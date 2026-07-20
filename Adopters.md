# Adopters

Projects that have adopted this ecosystem's templates, and a little context on how each came to use them. This file is for reading, not parsing — kept mostly for the Operator's own future nostalgia. Its structured, machine-parseable counterpart is `adopters.yaml`, which is what anything else (a future audit agent, a script) should read instead of this prose.

## Argus

Argus isn't really an adopter in the normal sense — it's where this pipeline came from. Every template in [[Templates/Agents]] and [[Templates/Skills]] started as a real agent or skill running in Argus's own `.claude/`, extracted and generalized once the underlying patterns (supervisor dispatch, adversarial audit, dependency verification before parallelizing) turned out to be project-agnostic rather than specific to Argus. See [[Timeline]] for the extraction, which happened on 2026-07-07.

As far as this registry is concerned, Argus is two repos:

- **[argus-product](https://github.com/yahordauksha/argus-product)** — the code repo, and the most complete live instance of this pipeline anywhere. Ten agent templates and five skill templates are installed on `main`, covering the whole implement → test → audit → PR cycle plus the vault-sync/ecosystem-health specialists. (`ecosystem-sync` itself is still in flight on an unmerged branch as of this writing — not yet on `main`, so not counted as installed here.)
- **[argus-docs](https://github.com/yahordauksha/argus-docs)** — a separate Obsidian vault for product-specific planning, not this pipeline's templates. It runs its own one-off `prep-foundations-gate` agent, unrelated to anything in this vault.

A third repo, `argus-landing`, exists but has no `.claude/` directory at all — not an adopter, left out of this registry for now.

## Map of Telegram

The first project onboarded through `/project-lifecycle`'s existing-unadopted (retrofit) branch (issue #63), 2026-07-16 — a solo side project (a channel-to-channel graph of public Telegram channels: Python crawler/export pipeline + TS/React/deck.gl frontend + a Cloudflare Worker production crawler on D1/Cron Triggers), previously real code with zero `.claude/` templates.

Eight agent templates and five skill templates installed on `main`: the full implement → test → audit → PR cycle (`core-implementer`, `test-writer`, `edge-case-auditor`, `implement`), `iac-specialist` (triggered by `worker/wrangler.toml`), `ops-check` (substantially rewritten against Cloudflare's `wrangler tail`/D1 tooling — its reference implementation was AWS-shaped), `doc-keeper` in Obsidian mode (the adoption run surfaced a real gap here — the vault's own `doc-keeper.md` had no Obsidian mode at all before this run; the Operator fixed the template directly mid-run, now v1.1.0), `ecosystem-sync`, and `ecosystem-diagnostician`. `triage`/`prompt-implementer`/`prompt-auditor`/`vault-sync`/`vault-auditor` weren't selected — no `.github/` directory existed yet (labels were created anyway, at the Operator's request), and this project isn't a prompt/agent-definition vault or a separate strategy vault (its docs live in the same repo, Obsidian-style).

doc-keeper's first AUDIT-mode run (dispatched as part of adoption) found real, live drift on the first try: three docs citing a stale cron cadence, a missing `Timeline.md` entry, and a stale "unverified" avatar-CDN claim that a same-repo doc had already resolved days earlier — all fixed with the Operator's authorization in the same session.

## Hermes

Onboarded through `/project-lifecycle`'s retrofit branch, 2026-07-20 — a solo personal-finance Telegram bot (Python 3.12 on AWS Lambda: poller/processor/receptor/watchdog, Supabase Postgres, Terraform IaC, GitHub Actions CI via OIDC), previously real code with zero `.claude/` templates. `CLAUDE.md` existed locally but had never actually been committed — the repo's own `.gitignore` excluded both `.claude/` and `CLAUDE.md` wholesale; the retrofit narrowed that exclusion to session-local state only (`settings.local.json`, `worktrees/`, `scheduled_tasks.lock`) so the installed templates and CLAUDE.md would actually be tracked.

Ten agent templates and five skill templates installed on `main`: the full implement → test → audit → PR cycle (`core-implementer`, `test-writer`, `edge-case-auditor`, `implement`), `iac-specialist` (extensive Terraform), `ops-check` (AWS/CloudWatch/Grafana Cloud — the reference implementation applied as-is, no provider swap needed), `triage` (GitHub Issues already actively used, issue numbers cited throughout the codebase), `doc-keeper` in Obsidian mode (the Operator's explicit choice — no docs/ directory existed, no wiki-link/callout or arc42 convention was already in use), `ecosystem-sync`, `ecosystem-diagnostician`, and `design-critic` (co-selected with `spec`). `prompt-implementer`/`prompt-auditor`/`vault-sync`/`vault-auditor` weren't selected — Hermes is a finance-bot application, not itself a prompt/agent-definition vault or a separate strategy vault.

The Operator scoped this project's safety surface deliberately narrow: only the financial schema & data-isolation cluster (`supabase/migrations/*.sql`, RLS policies, `lambdas/shared/crypto.py`, and a known plaintext-payload gap in `transactions.raw_ob_payload`) is "never touch autonomously." Several other real findings from evidence-gathering — broad CI deploy-role IAM permissions, an unattended Terraform state force-unlock in CI, real personal financial data seeded in dev migrations — were surfaced and reviewed but intentionally left outside that gate.

doc-keeper's first AUDIT-mode run found no `docs/` directory at all; it bootstrapped `Home.md`, `Architecture.md` (seeded from the README's data-flow diagram plus still-accurate design content pulled from an archived historical design doc, verified against the real code rather than copied blindly), and an empty `Timeline.md` to start recording decisions going forward.

## Related

- [[Timeline]] — the extraction this file's Argus entry refers to
- `adopters.yaml` — the structured counterpart to this file
