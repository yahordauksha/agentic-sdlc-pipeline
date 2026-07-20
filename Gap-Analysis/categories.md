# Prior-Art Categories

The living "what to check" list for [[.claude/commands/gap-analysis]]. Read fresh every run — this file grows over time (each entry born either from issue #24's seed list below, or appended by `gap-analysis` itself after asking `deep-research` what's newly relevant, with a one-line reason). `gap-analysis.md` itself should never need editing as the field evolves; only this file grows.

## Agentic design patterns

- Anthropic, "Building Effective Agents" — names orchestrator-workers and evaluator-optimizer as core agentic shapes.

_Seeded from issue #24: `implement` dispatching specialists is orchestrator-workers; `edge-case-auditor`'s fix-then-reaudit loop is evaluator-optimizer._

## Multi-agent orchestration frameworks

- LangGraph
- CrewAI
- AutoGen / AG2
- OpenAI Agents SDK (formerly Swarm)

_Seeded from issue #24: check whether these have already solved problems this vault is solving ad hoc._

## Agentic coding prior art

- SWE-agent / SWE-bench
- Aider
- OpenHands
- Cognition (Devin) engineering blog posts
- SWE-Bench Pro — 1,865-instance successor to SWE-Bench Verified across 41 repos (731 public + 858 held-out + 276 commercial), built as frontier models saturated the older benchmark.
- Terminal-Bench / Harbor (Stanford x Anthropic) — realistic terminal/CLI task benchmark on a containerized ("Harbor") evaluation framework, actively iterated (1.0→2.0/2.1→3.0) with a live public leaderboard.

_Added 2026-07-15 (first `/gap-analysis` run): frontier models saturated SWE-Bench Verified, so agentic-coding evaluation moved to these harder, less-contaminated successors. Sources: https://scale.com/blog/swe-bench-pro, https://www.tbench.ai/_

_Seeded from issue #24._

## Durable/resumable execution

- Temporal — the mature pattern for durable, resumable workflow execution.

_Seeded from issue #24: `implement`'s hand-rolled worktree-resume-on-bail logic reinvents a narrow slice of this._

## Memory management

- MemGPT / Letta — hierarchical memory patterns.
- Zep / Graphiti — temporally-aware knowledge-graph memory engine; graph-based alternative to MemGPT/Letta's approach.
- Mem0 — latency/cost-optimized memory architecture (published ~91% lower p95 latency than full-context processing, roughly accuracy-competitive).
- MIRIX — six-component multi-agent memory system (Core, Episodic, Semantic, Procedural, Resource, Knowledge Vault), one dedicated agent per component.

_Added 2026-07-15 (first `/gap-analysis` run): LLM memory systems have diversified well beyond MemGPT/Letta into a competitive landscape with distinct architectures and published tradeoffs. Sources: https://arxiv.org/abs/2501.13956 (Graphiti), https://arxiv.org/pdf/2504.19413 (Mem0), https://arxiv.org/pdf/2507.07957 (MIRIX, self-reported benchmark — treat accuracy/storage claims as vendor-reported, not independently verified)._

_Seeded from issue #24: relevant if any agent here ever needs state across more than one session._

## Guardrails / safety

- Guardrails AI
- NeMo Guardrails
- OWASP Top 10 for LLM Applications
- Cloud Security Alliance MCP Security Best Practices — six MCP-specific threat categories (pre-auth RCE, tool poisoning, rug pulls, session hijacking, supply chain attacks, cross-tenant leakage), tied to 30+ CVEs since Jan 2026; mandates OAuth 2.1 + TLS 1.2+ for remote MCP servers.
- MAESTRO (Cloud Security Alliance) — threat-modeling framework for agentic AI specifically, extending STRIDE/PASTA/LINDDUN-style modeling across 7 architectural layers of a multi-agent system.
- LlamaFirewall (Meta) — open-source guardrail framework; its Agent Alignment Checks component is a chain-of-thought auditor for detecting goal hijacking/injection-induced misalignment.

_Added 2026-07-15 (first `/gap-analysis` run): MCP's rapid real-world adoption created a fast-moving, protocol-specific threat surface that Guardrails AI/NeMo Guardrails/OWASP LLM Top 10 don't cover protocol-specifically. Sources: https://labs.cloudsecurityalliance.org/agentic/agentic-mcp-security-best-practices-v1/, https://cloudsecurityalliance.org/blog/2025/02/06/agentic-ai-threat-modeling-framework-maestro, https://arxiv.org/pdf/2505.03574 (LlamaFirewall)._

_Seeded from issue #24._

## Opinionated multi-agent SDLC pipeline frameworks

- BMAD-METHOD (bmad-code-org) — role-based agents (PM/Architect/Dev/QA) producing persistent, versioned artifacts (PRDs, architecture docs, story files) with quality gates between phases; expansion packs port domain knowledge into new projects. 43K+ stars. Has a direct Claude Code port (24601/BMAD-AT-CLAUDE).
- GitHub Spec Kit (github/spec-kit) — official GitHub toolkit: specify → plan → tasks → implement, with human checkpoints between phases.
- Agent OS (buildermethods/agent-os) — injects durable codebase standards into agent context (`/discover-standards`, `/inject-standards`); actively evolving, v3 shipped 2026.
- Specky (paulasilvatech/specky) — 13 specialized agents behind a deterministic 10-phase enforced pipeline, meeting-transcript-to-PR.
- MetaGPT (FoundationAgents/MetaGPT) — the original of this pattern: PM/Architect/PM/Engineer/QA roles with SOPs between them. Standalone Python framework, not built for a coding agent's file-based agent/skill system — useful for design ideas, not directly adoptable.

_Added 2026-07-16, prompted by the Operator asking whether this vault's own pipeline is redundant with existing prior art: distinct from "Multi-agent orchestration frameworks" above (LangGraph/CrewAI/AutoGen/OpenAI Agents SDK are generic orchestration libraries) — these are opinionated, spec-driven SDLC pipelines with persistent doc artifacts, the same shape this vault's `spec.md`/`implement.md`/ADR pattern is. BMAD-METHOD in particular is the closest match found to date, closer than `superflow`. Sources: https://github.com/bmad-code-org/bmad-method, https://github.com/github/spec-kit, https://github.com/buildermethods/agent-os, https://github.com/paulasilvatech/specky, https://github.com/FoundationAgents/MetaGPT._

## Interoperability / Standardization Protocols

- MCP (Model Context Protocol, Anthropic) — JSON-RPC client-server protocol standardizing agent-to-tool context ingestion and invocation (Tools, Resources, Prompts, Sampling primitives). Now under a Linux Foundation-governed Agentic AI Foundation (Anthropic/Google/OpenAI/Microsoft/AWS/Block).
- A2A (Agent2Agent Protocol, Google) — protocol for inter-agent (horizontal) communication, positioned as complementary to MCP's agent-to-tool (vertical) standardization. Combining A2A discovery with MCP execution creates compounded security risks distinct from either alone (e.g. MCP "tool squatting" becomes more dangerous when paired with A2A's discovery surface).

_Added 2026-07-15 (first `/gap-analysis` run) as a new 7th category — this vault's agents currently have no concept of cross-project or cross-vendor agent interoperability (every agent/skill here is bespoke to this pipeline's own dispatch conventions); MCP/A2A are the emerging industry standard for that gap, worth watching even though no concrete adoption case exists yet. Sources: https://arxiv.org/html/2505.02279v1 (MCP), https://arxiv.org/pdf/2505.03864 (A2A + MCP combined risk)._

## Related

- [[Principles]]
- [[Timeline]]
