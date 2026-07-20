---
allowed-tools: Bash(<pipeline-scripts>:*), Bash(<issue-tracker> issue list:*), Bash(<issue-tracker> issue view:*), Bash(<issue-tracker> issue comment:*), Bash(<issue-tracker> issue create:*), Bash(<issue-tracker> pr list:*), Bash(<issue-tracker> api:*), Read, Grep, Glob, Artifact, Agent
description: Periodic manual sweep over the pipeline's own structured event log — regenerates a pipeline dashboard if one exists, re-checks the whole log for recurring bail/spec-question patterns the automatic per-event trigger might have missed, correlates past spec_question/decision events against downstream evidence to draft decision_outcome verdicts, reviews token/CI/cloud resource efficiency, and does a broader read for cross-cutting signals no exact-label match can see. Invoke on demand; not part of the implementation supervisor's or spec skill's automatic flow.
model: sonnet
version: 1.0.1
---

> Version 1.0.1

You are doing a periodic health check on **[CUSTOMIZE: project name]**'s own implementation pipeline — not a product issue, the pipeline itself (the implementation supervisor, the spec skill, `ecosystem-diagnostician`). This is the manual, broad-sweep counterpart to the automatic, narrow checks that already run inline: the supervisor's bail-handling step and the spec skill's own escalation step each check one new event against prior history at the moment it happens, using an *exact* label match (`stage`+`blocker_type` for bails, `category` for spec questions). That precision is deliberate — a false "recurring" burns Operator trust worse than a missed one — but it structurally cannot see anything that isn't an exact repeat. This skill is where the wider, occasional look happens instead, the same relationship `vault-auditor` has to `vault-sync`: automatic and narrow runs constantly, manual and broad runs when invoked.

**Context provided:** $ARGUMENTS (none needed — always operates over the full pipeline event log)

> [!note] [CUSTOMIZE] This skill assumes a JSONL structured event log (e.g. `PIPELINE_LOG.jsonl`), written on every bail/spec-question/pr-opened event, plus a handful of small Python helper scripts for the mechanical steps below. The sanctioned write mechanism — a bash+`jq` emission script paired with a `PreToolUse` guardrail hook denying direct writes to the log outside that script — is templated in full, with a worked example and the exact event schema it was checked against, in [[Templates/Hooks/README]]. See [[Principles#Curated judgment and raw telemetry are two different logging problems, not one]] for why a hook can mechanize the write but never the judgment behind it. This is not optional for STEP 3b/STEP 3c below: once this guardrail is adopted, STEP 3b's `decision_outcome` append and STEP 3c's `ecosystem_fix_applied` append route through the same sanctioned script like every other event — they are not a separate ad hoc write path exempt from it. The schema this skill reads is unaffected either way. If your project doesn't have this log yet, start it before adopting this skill — see [[Principles]]'s open questions on this capture layer and on cross-project pipeline telemetry for the schema shape.

---

## STEP 1 — Regenerate and republish the dashboard (if one exists)

```bash
<dashboard-generator-script>
```

If your project publishes this as a live Artifact, read the script's own reference for the current published URL and publish in place (same `url`) rather than minting a new one each run. If the script errors (missing asset, unreadable log), stop and report — do not proceed to STEP 2 on stale or absent data. If your project has no dashboard yet, skip this step entirely.

---

## STEP 2 — Full-log exact-match sweep (mechanical, no agent yet)

This is a consistency check on the automatic mechanism itself, not a new detection method — it re-runs the same exact-match logic the supervisor's bail-handling step and the spec skill's escalation step already apply incrementally, but over the whole log at once, to catch anything a buggy or skipped inline check might have missed.

```bash
python3 -c "
import json
from collections import defaultdict

bails, questions = [], []
with open('<pipeline-log-path>') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        e = json.loads(line)
        if e.get('event') == 'bail':
            bails.append(e)
        elif e.get('event') == 'spec_question':
            questions.append(e)

by_label = defaultdict(list)
for b in bails:
    by_label[(b.get('stage'), b.get('blocker_type'))].append(b)
print('BAIL GROUPS (size >= 2):')
for label, group in by_label.items():
    if len(group) >= 2:
        print(label, [ (g['issue'], g.get('recurrence_verdict'), g.get('tracking_issue')) for g in group ])

by_cat = defaultdict(list)
for q in questions:
    by_cat[q.get('category')].append(q)
print('QUESTION GROUPS (size >= 2):')
for cat, group in by_cat.items():
    if len(group) >= 2:
        print(cat, [ (g['issue'], g.get('recurrence_verdict'), g.get('tracking_issue')) for g in group ])
"
```

For each group of size ≥2 printed above:
- If every member already shows `recurrence_verdict: "recurring"` with a non-null `tracking_issue`, or `"not_recurring"` — the automatic mechanism already handled this correctly. Nothing to do.
- If any member shows `"not_checked"` where a same-labeled prior event existed **before** it chronologically — the automatic per-event check was skipped or broken for that event. This is itself a finding: note it for the report (STEP 5) as a gap in the automatic mechanism, separate from whatever the underlying bail/question pattern turns out to be. Then treat the whole group as needing STEP 4's diagnostician pass, since it was never actually judged.

---

## STEP 3 — Broader read: cross-cutting signals no exact-label match can see

Exact-label matching is blind to anything that isn't a literal repeat of the same `stage`+`blocker_type` or `category`. Read the full log yourself and look for patterns that only show up in aggregate — for example (not exhaustive, use judgment on what's actually in the data):

- A `blocker_type` that dominates bails **across different stages** (an exact-match check would never flag this, since stage differs each time).
- A single issue needing multiple bail→spec-recovery cycles, even with genuinely different causes each time (not a "recurring" verdict on its own, but worth surfacing if it keeps happening on the same issue).
- The edge-case-auditor's zero-fix-round rate trending down, or staying at 0 — a process-quality signal distinct from any single bail.
- Cycle time or token cost outliers for a given event type, once there's enough history to call something an outlier rather than normal variance.
- The spec-invoked rate relative to total implementation attempts.

**Apply a sample-size floor before treating anything here as actionable.** With single digits of bails/questions total, note an observation as "worth watching" in the report, explicitly with the current count, and stop there — do not draft a fix or open a tracking issue off a sample this small. A reasonable floor: at least 5 occurrences of whatever you're generalizing about before calling it a pattern rather than noise. State your reasoning plainly if you do treat something below that floor as worth escalating anyway — don't apply the floor mechanically if the signal is otherwise unambiguous (e.g. the exact same issue bailing 3 times in a row on the same file is worth flagging at n=3).

Findings here do **not** automatically route through `ecosystem-diagnostician` — its brief format is built for exact-label recurrence judgment (`kind: bail` / `kind: spec-question`), not general statistical review, and forcing a cross-cutting observation into that shape would misrepresent what was actually found. Report these directly in STEP 5 instead, hedged appropriately. If a cross-cutting read surfaces something that *does* reduce to an exact-label question in disguise (e.g. you notice a stage+blocker_type pair STEP 2's grep missed because of a labeling inconsistency), fix the grouping and route it through STEP 4 properly rather than reporting it as a soft observation.

---

## STEP 3b — Decision-outcome correlation pass

`spec_question` and `decision` events capture what was decided and why, but nothing else in the pipeline ever revisits whether the decision held up. This step is that missing half — it runs every time this skill runs, with no separate trigger, since expecting a human to remember to check on a decision made weeks or months ago is exactly the gap this closes.

1. **Collect candidates** (mechanical, no agent) — every `spec_question`/`decision` with no matching `decision_outcome` yet (matched by `issue`+`category`), old enough that downstream evidence has had a chance to accumulate:

```bash
python3 <collect-outcome-candidates-script> spec_question,decision issue,category
```

2. **Gather evidence per candidate** — `<issue-tracker> issue view <issue>` for reopens, follow-up comments, or linked PRs referencing it; a PR search for revert/hotfix PRs that reference it without necessarily linking back through the issue itself; a grep of the pipeline log for later `bail`/`incident`/`spec_question`/`decision` events sharing the same `category` or touching the same area; whether the originating PR (or a later PR touching the same files) needed an edge-case-auditor fix cycle (visible on the matching `pr_opened` line). Do this judgment directly yourself, the same way STEP 3 reads the log directly — do **not** route it through `ecosystem-diagnostician`: that agent's brief format is built specifically for exact-label recurrence judgment, not evidence-weighing for a good/bad verdict.

3. **Draft a verdict** — `good` (no contradicting evidence, or evidence explicitly favorable), `bad` (reverted, caused an incident, or triggered a later bail), `mixed`, or `inconclusive` (too little downstream activity in that area to say either way). Set `confidence` honestly: an absence-based `good` (nothing went wrong, but the area also hasn't seen much activity since) is `low` confidence, not `high` — don't let a clean-looking draft imply more certainty than the evidence supports.

4. **Confirm before writing.** Present every draft in this run's STEP 5 report. Only append a `decision_outcome` line — with `confirmed_by_operator: true` — once the Operator confirms it in this session (verbatim or as edited). Never append one speculatively; an unconfirmed draft that never gets Operator attention simply stays a candidate for the next run, it does not get written as a guess.

---

## STEP 3c — Ecosystem-fix-outcome correlation pass

Ecosystem-fix issues get opened when a recurring bail or spec_question is diagnosed, but nothing else in the pipeline ever revisits whether the drafted fix actually worked once applied. This step closes that loop — structured like STEP 3b, but the "was this decision recorded" half is derived mechanically instead of trusted to a human log line, since applying a fix is a rare, spaced-out action that's easy to forget to log by hand.

### 1. Detect newly-applied fixes (mechanical, no agent)

List closed ecosystem-fix issues and cross-check each against the pipeline log:

```bash
<issue-tracker> issue list --label "type:ecosystem-fix" --state closed \
  --json number,title,stateReason,closedByPullRequestsReferences --limit 200
```

For each issue number not already present as an `ecosystem_fix_applied` line's `issue` field in the log:

- Skip it if `stateReason` is not `"completed"` (a wontfix/duplicate close correctly means no fix was ever applied; not an anomaly, just nothing to record).
- If `stateReason` is `"completed"`, check `closedByPullRequestsReferences` for a merged PR. Confirm it actually touches a relevant file (`.claude/agents/`, `.claude/commands/`, `CLAUDE.md`, or the vault's Decision Policy doc).
  - **Found and confirmed** — parse the issue title against the exact conventions STEP 4 writes: "Recurring bail: `<stage>/<blocker_type>`" → `origin: diagnostician_bail`; "Recurring spec question: `<category>`" → `origin: diagnostician_question`; anything else → `origin: manual`. Append `ecosystem_fix_applied` with `ts` = the PR's merge time, `closing_pr` = the PR number, and a one-line summary. No Operator confirmation needed — this is a recorded fact (issue closed, PR merged, file touched), not a judgment.
  - **Completed but no matching merged PR/file touch found** — do **not** log `ecosystem_fix_applied`. Note it for STEP 5 instead.

### 2. Collect outcome candidates (mechanical, no agent)

Same shape as STEP 3b's script, over `ecosystem_fix_applied` instead of `spec_question`/`decision`, matched by `issue` alone, same delay floor:

```bash
python3 <collect-outcome-candidates-script> ecosystem_fix_applied issue ecosystem_fix_applied
```

### 3. Gather evidence per candidate

- `origin: diagnostician_bail` / `diagnostician_question` — grep the pipeline log for any `bail`/`spec_question` event **after** this fix's `ts` sharing the exact `ref_stage`+`ref_blocker_type` (or `ref_category`). This is the precise check: an exact-label repeat after the fix landed means the fix didn't address the root cause.
- `origin: manual` — no exact label exists to grep. Fall back to reading the issue/PR to judge whether the described change actually materialized and is in use. This is a judgment read, not a mechanical match.

### 4. Draft a verdict

`good` (no exact-label repeat since, with enough subsequent same-type activity to make that meaningful), `bad` (same label recurred anyway, or a later issue/comment explicitly says this fix didn't hold), `mixed`, or `inconclusive`. Same absence caution as STEP 3b.

### 5. Confirm before writing

Present every draft in this run's STEP 5 report. Only append the `decision_outcome` line once the Operator confirms it, verbatim or edited, in this session.

---

## STEP 4 — Diagnose and act on exact-match findings

For every group flagged by STEP 2 (and any STEP 3 finding that turned out to genuinely be an exact-label match):

Dispatch `ecosystem-diagnostician` with the same brief shape the supervisor/spec skill already use — this run's context plus every member of the group. Let it judge NOT-RECURRING vs RECURRING exactly as it does inline — do not skip its judgment just because this is a periodic sweep instead of an inline trigger.

On **RECURRING**, before opening a new tracking issue, check whether one already exists for this exact pattern:
```bash
<issue-tracker> issue list --label "type:ecosystem-fix" --state all --search "Recurring bail: <stage>/<blocker_type>"
# or, for a question category:
<issue-tracker> issue list --label "type:ecosystem-fix" --state all --search "Recurring spec question: <category>"
```
If a matching issue is already open or closed, do not duplicate it — reference the existing one in the STEP 5 report instead. Only if none exists: post the comment defined in [[Templates/GitHub/comment-templates#Recurring-pattern comment]] on every issue in the group, and open one new ecosystem-fix tracking issue in the exact shape defined in [[Templates/GitHub/issue-templates#Ecosystem-fix tracking issue]] — the title convention there is what the dedup search above (and this skill's own future dedup checks) depends on matching exactly.

On **NOT-RECURRING**, note it in the report — this is a legitimate outcome, not a failure of the sweep.

---

## STEP 4b — Resource efficiency review

A different question than STEP 1-4: not "is the pipeline behaving correctly" but "is what it's spending — tokens, CI minutes, cloud cost — proportional to what it's buying, and is there a reduction available that costs nothing." Runs every time this skill runs, same cadence as STEP 3b/3c and for the same reason: nobody reliably remembers to check this by hand.

### 1. Token spend trend (mechanical)

Adapt the script below to your log's actual field names (this assumes `token_measurement`/`output_tokens` fields on each event, as the implementation supervisor logs them):

```bash
python3 -c "
import json
from datetime import datetime, timezone, timedelta
from collections import defaultdict

events = []
with open('<pipeline-log-path>') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        e = json.loads(line)
        if e.get('token_measurement') == 'measured' and e.get('output_tokens'):
            events.append(e)

def ts_of(e):
    t = e.get('ts_end') or e.get('ts')
    return datetime.fromisoformat(t.replace('Z', '+00:00')) if t else None

now = datetime.now(timezone.utc)
cutoff, prior_cutoff = now - timedelta(days=14), now - timedelta(days=28)

by_type = defaultdict(lambda: {'current': [], 'prior': []})
for e in events:
    t = ts_of(e)
    if not t:
        continue
    bucket = by_type[e['event']]
    (bucket['current'] if t >= cutoff else bucket['prior'] if t >= prior_cutoff else []).append(e['output_tokens'])

for etype, b in by_type.items():
    cur_avg = sum(b['current']) / len(b['current']) if b['current'] else 0
    prior_avg = sum(b['prior']) / len(b['prior']) if b['prior'] else 0
    print(f'{etype}: n={len(b[\"current\"])} avg_output_tokens={cur_avg:.0f} (prior 14d: n={len(b[\"prior\"])} avg={prior_avg:.0f})')

all_by_type = defaultdict(list)
for e in events:
    all_by_type[e['event']].append(e)
for etype, es in all_by_type.items():
    if len(es) < 5:
        continue
    avg = sum(e['output_tokens'] for e in es) / len(es)
    for e in es:
        if e['output_tokens'] > 2 * avg:
            print(f'OUTLIER: {etype} issue={e.get(\"issue\")} output_tokens={e[\"output_tokens\"]} (2x trailing avg={avg:.0f}, n={len(es)})')
"
```

Apply the same ≥5-occurrence floor as STEP 3 before calling anything a trend rather than noise.

### 2. CI volume/cost trend (mechanical)

[CUSTOMIZE] Adapt to your CI provider. For each workflow (at minimum [[Templates/CI/README|`ci`]], plus any this project has added beyond it), pull run counts for the current and prior 14-day windows, sample a few recent runs for a current cost-per-run estimate, and compare estimated total minutes/cost this window vs. the prior window.

**Proportionality, not just growth.** Pull this window's `pr_opened` count from the pipeline log as the volume denominator. CI-minutes growth roughly matching PR-volume growth is expected, not a finding — minutes growing *faster* than PR volume is the actual signal, since that means something got less efficient, not just busier.

### 3. Cloud cost/efficiency — dispatch `ops-check`

Dispatch the `ops-check` agent in cost-efficiency mode: `"mode: cost-efficiency, window: last 30 days"`. Fold its terminal summary directly into this run's STEP 5 report under its own section — do not re-derive or second-guess its findings, it owns cloud read access and judgment for that domain, the same way STEP 4 defers to `ecosystem-diagnostician`'s judgment on recurrence rather than re-deciding it.

### 4. Classify and act

Classify every token/CI finding the same two ways `ops-check` classifies its own:
- 🟢 **FREE WIN** — a reduction with no functional or coverage sacrifice (e.g. jobs billed a minimum for sub-minute work that could be consolidated).
- 🟡 **TRADEOFF** — a reduction that costs something and needs the Operator's judgment.

For a systemic finding (recurring across runs, not a one-off), open an ecosystem-fix tracking issue — same dedup-by-title-search discipline as STEP 4. A one-off outlier (a single expensive run) is reported, not tracked, unless it recurs.

---

## STEP 5 — Report

Terminal report, similar shape to `queue-scout`'s:

```
PIPELINE REVIEW — <N> events checked, dashboard refreshed at <url, if applicable>

✅ EXACT-MATCH SWEEP — clean:
  No stage+blocker_type or category group of size ≥2 found beyond what's already tracked.

⚠️ AUTOMATIC-CHECK GAP FOUND:
  #<issue> <stage>/<blocker_type> — recurrence_verdict was "not_checked" despite a same-labeled
  prior bail (#<prior-issue>, <date>) already existing at the time. <your read on why, if apparent>.

🔁 RECURRING — new tracking issue opened:
  <stage>/<blocker_type> or <category> — #<tracking-issue>, instances: #<issue>, #<issue>

🔁 RECURRING — already tracked, no duplicate opened:
  <stage>/<blocker_type> — see existing #<tracking-issue>

◻️ NOT-RECURRING — label matched, cause didn't:
  #<issue>, #<issue> — <one-line reason from the diagnostician>

👁 WORTH WATCHING — below the sample-size floor, not actioned:
  <observation> (n=<count>) — revisit once there's more history

🗳 DECISION OUTCOME — awaiting your confirmation:
  #<issue> [<category>] "<summary>" — draft verdict: <verdict> (confidence: <level>)
  Evidence: <citation>, <citation>
  Confirm as-is, edit, or skip this cycle?

✅ DECISION OUTCOME — confirmed and logged:
  #<issue> [<category>] — <verdict> (confidence: <level>)

❓ ECOSYSTEM-FIX ISSUE CLOSED, NO LINKED CHANGE FOUND:
  #<issue> — closed <date>, no merged PR found touching the drafted file. Applied outside the normal PR flow, or closed in error?

🔧 ECOSYSTEM-FIX OUTCOME — awaiting your confirmation:
  #<tracking-issue> (<origin>) "<summary>" — draft verdict: <verdict> (confidence: <level>)
  Evidence: <citation>, <citation>
  Confirm as-is, edit, or skip this cycle?

✅ ECOSYSTEM-FIX OUTCOME — confirmed and logged:
  #<tracking-issue> (<origin>) — <verdict> (confidence: <level>)

💰 RESOURCE EFFICIENCY — token spend:
  <event type>: avg <N> output tokens/run (prior window: <N>) — <flat|up X%|down X%>
  OUTLIER: #<issue> <event type> — <N> tokens, 2x trailing average — <your read on why, if apparent>

💰 RESOURCE EFFICIENCY — CI:
  <workflow>: ~<N> runs, ~<N> billed min this window (prior: ~<N> runs, ~<N> min) — <proportional to PR volume | growing faster than PR volume>

💰 RESOURCE EFFICIENCY — cloud (via ops-check):
  <ops-check's cost-efficiency terminal summary, verbatim or lightly trimmed>

🟢 FREE WIN:
  <finding> — <what it saves, why nothing is sacrificed>

🟡 TRADEOFF — needs your call:
  <finding> — <what it saves, what it costs, why it's not a free win>

Recommended next action: <e.g. "nothing needs Operator time this cycle" or "review the new tracking issue #<n> when convenient">
```

If everything is clean and no observations clear even the "worth watching" bar, say so plainly — don't pad the report to look thorough.

---

## HARD RULES

- Never edit `.claude/agents/*`, `.claude/commands/*`, `CLAUDE.md`, or the vault's Decision Policy doc yourself — same discipline as `ecosystem-diagnostician` and the supervisor/spec skill's own handling of its output. Drafted fixes are always a tracking-issue proposal, never a same-run write.
- Never open a duplicate ecosystem-fix tracking issue — always check by title pattern first.
- Never force a STEP 3 cross-cutting observation through `ecosystem-diagnostician`'s bail/spec-question brief format — report it directly instead.
- Never treat a small sample as a confirmed pattern — state the count, apply the floor, say "worth watching" when that's honestly all it is.
- Never append a `decision_outcome` line — whether from STEP 3b or STEP 3c — without that specific verdict being confirmed by the Operator in this session. A drafted verdict the Operator doesn't get to in this run stays a candidate for next time, it is not written as a best guess.
- Never append `ecosystem_fix_applied` for a closed ecosystem-fix issue without confirming both a completed-state close and a merged PR that actually touches the drafted file — a close with neither is an anomaly to surface (STEP 3c), not a fix to record.
- This skill does not replace the inline checks in the supervisor's bail-handling step or the spec skill's escalation step — those still run automatically on every bail/question. This is the periodic wide-angle pass on top, not a substitute for either.
- Never classify a STEP 4b finding as a 🟢 free win without stating why nothing is sacrificed — if there's any real doubt, it's a 🟡 tradeoff, not a free win.
- Never route an `ops-check` cloud cost/right-sizing finding through the pipeline's own self-improvement label — that's for the pipeline's own tooling; cloud/product-infra findings use `ops-check`'s own issue convention, which it applies itself.
- Apply the same sample-size floor to STEP 4b's token/CI trends as STEP 3 already applies to bail patterns — a single outlier run is noise until it happens enough to call a trend.
- STEP 4b never edits any workflow or config file itself, same as this skill never edits `.claude/agents/*`/`.claude/commands/*` — a 🟢 free win is still a tracking-issue proposal for the Operator to apply, not a same-run write.

## Related

- [[Principles]]
- [[Templates/Agents/ecosystem-diagnostician]]
- [[Templates/Agents/ops-check]]
- [[Templates/Agents/vault-auditor]] — the same automatic-narrow/manual-broad relationship, applied to the strategy vault instead of the pipeline log
- [[Templates/Skills/implement]]
- [[Templates/Skills/spec]]
- [[Templates/GitHub/comment-templates]]
- [[Templates/GitHub/issue-templates]]
- [[Templates/CI/README]]
- [[Templates/Hooks/README]] — the sanctioned emission script + guardrail hook this skill's own log-write mechanism is templated in
