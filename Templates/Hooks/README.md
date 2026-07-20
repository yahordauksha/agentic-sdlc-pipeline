# Hooks Template: Mechanized Writes for a Curated Pipeline Event Log

The write-path pattern [[Principles#Curated judgment and raw telemetry are two different logging problems, not one]] calls for but doesn't itself template: a hook can mechanize *how* a judgment reaches disk, never the judgment itself. This doc is that template — a worked, concrete example, not another prose description of the idea. See [[Principles#Shared shapes need one definition, not one description per reader]] for why this belongs written down once rather than re-described by every caller.

> [!note] Vault ships templates, not live project code
> This is a `[CUSTOMIZE]`-tagged pattern for an adopting project's own `.claude/settings.json` and `scripts/`. Wiring it into any specific project's live pipeline is separate, later work in that project's own repo — same relationship [[Templates/CI/README]] has to a project's actual `ci.yml`.

## The precedent this already extends: `worktree_violation_caught`

A `PreToolUse` hook, matched on `Bash`, already exists in production for one event: it denies a direct `git commit` on `main` and, in the same hook invocation, mechanically appends a `worktree_violation_caught` line via `jq` — zero agent involvement. This works because every field that event needs (`caught_by`, `files`, a summary of what was denied) is derivable entirely from the raw tool call the hook is already inspecting. Nothing about that hook needs to change; it's the concrete proof this pattern already works, not a hypothesis.

`bail`, `spec_question`, `decision`, and the rest of a curated pipeline log are different in kind: `stage`, `blocker_type`, `category`, `recurrence_verdict` are judgment calls an agent makes, not something inferable from a raw tool call. No hook can produce them. What follows mechanizes the *write* of that judgment, once an agent has already decided what it is.

## The pattern: a sanctioned emission script + a guardrail hook

Two pieces, used together:

1. **`emit-pipeline-event.sh`** — the only sanctioned writer. Agents call it instead of hand-composing JSON. Built on the same mechanics as superflow's `sf-emit.sh`: a typed `key=val` / `key:int=val` / `key:bool=val` / `key:json=val` argument DSL, event JSON constructed entirely through `jq --arg`/`--argjson` — never shell string interpolation — so an unescaped quote in a `summary` field can't break the JSON or, worse, escape into something else. Every event type is checked against an explicit allowlist and every key name against a regex before anything is written. Threshold-based rotation to an `archive/` subdirectory keeps the file from growing unbounded, the same default superflow ships (5000 lines).
2. **A `PreToolUse` guardrail hook**, matched on `Bash`, that denies a literal write to the log file (a redirect, `jq ... > file`, `sed -i`, a Python `open(..., 'a')`) that doesn't go through that script — the same shape as the `worktree_violation_caught` hook above, just generalized from one event to the full vocabulary.

**Both fail loud, on purpose — not fail-open like `sf-emit.sh`.** A malformed argument, an unrecognized event type, an unwritable log path, or a hook that can't parse its own input all exit nonzero / block the tool call and say why. A logging path that silently no-ops the moment something's misconfigured is worse than one that never existed, because nothing downstream knows to look for the gap. See [[Principles#Fail loud, disclose by default]].

> [!important] The guardrail blocks the bypass, not ad hoc logging itself
> [CUSTOMIZE]'s own schema doc for this project should say the same thing Argus's does: any session acting as supervisor may log `note`/`incident`/`decision` "by hand." The guardrail below does not make that harder — it makes the *sanctioned script* the one path, and calling that script by hand is exactly as simple as it always was: one shell command with typed arguments, e.g. `scripts/emit-pipeline-event.sh event=note issue=42 summary="checked in on the queue, nothing blocking"`. What the guardrail actually removes is the *other* option — hand-composing a JSON line and redirecting it into the file directly — which is exactly the fragile path this pattern replaces. If a narrower guardrail ever turns out to be needed (e.g. because some legitimate ad hoc write pattern doesn't fit the script's argument shape), scope the hook's deny pattern down to the specific bail/spec_question-shaped writes it's actually meant to catch, rather than shipping a blanket deny-all-other-writes rule — see [[Principles#Guardrails need an anchor outside the agent's own context, not just good prompting]] for why an over-tight guardrail that gets silently worked around is worse than a narrower one that's actually followed.

### `emit-pipeline-event.sh` — worked example

```bash
#!/usr/bin/env bash
# emit-pipeline-event.sh — the one sanctioned writer for PIPELINE_LOG.jsonl.
# [CUSTOMIZE] EVENT_TYPES to this project's own schema doc - the first 14
# event types below are argus-product's docs/PIPELINE_LOG_SCHEMA.md, verbatim;
# design_exploration_offered/design_exploration_declined are this vault's own
# later addition (spec.md's STEP 1c, #76 Wave 2), not part of Argus's original
# set. Do not copy this list into a project with a different schema without
# checking which of these 16 your own project actually needs.
set -euo pipefail

LOG_PATH="${PIPELINE_LOG_PATH:-PIPELINE_LOG.jsonl}"                # [CUSTOMIZE] path
ROTATE_THRESHOLD="${PIPELINE_LOG_ROTATE_THRESHOLD:-5000}"          # [CUSTOMIZE] lines - sf-emit.sh's own default
ARCHIVE_DIR="$(dirname "$LOG_PATH")/archive"

EVENT_TYPES="bail spec_invoked pr_opened needs_decision spec_question decision decision_outcome ecosystem_fix_applied spec_resolved spec_completed requeued incident note worktree_violation_caught design_exploration_offered design_exploration_declined"
KEY_RE='^[a-z][a-z0-9_]*$'

fail() { echo "emit-pipeline-event: FATAL: $*" >&2; exit 1; }

[ $# -ge 1 ] || fail "usage: $0 event=<type> key=val key:int=val key:bool=val key:json=val ..."

event=""
args=()
for arg in "$@"; do
  case "$arg" in
    event=*) event="${arg#event=}" ;;
    *) args+=("$arg") ;;
  esac
done

[ -n "$event" ] || fail "missing required event=<type> argument"
echo "$EVENT_TYPES" | tr ' ' '\n' | grep -qx "$event" \
  || fail "'$event' is not in the allowlisted event-type list: $EVENT_TYPES"

jq_args=(--arg event "$event")
jq_filter='{event: $event}'

for arg in "${args[@]}"; do
  case "$arg" in
    *:int=*)
      key="${arg%%:int=*}"; val="${arg#*:int=}"
      [[ "$key" =~ $KEY_RE ]] || fail "invalid key name: '$key'"
      jq_filter+=" | .[\"$key\"] = (\$${key}_int | tonumber)"
      jq_args+=(--arg "${key}_int" "$val")
      ;;
    *:bool=*)
      key="${arg%%:bool=*}"; val="${arg#*:bool=}"
      [[ "$key" =~ $KEY_RE ]] || fail "invalid key name: '$key'"
      [[ "$val" == "true" || "$val" == "false" ]] || fail "'$key:bool' must be true or false, got '$val'"
      jq_filter+=" | .[\"$key\"] = (\$${key}_bool == \"true\")"
      jq_args+=(--arg "${key}_bool" "$val")
      ;;
    *:json=*)
      key="${arg%%:json=*}"; val="${arg#*:json=}"
      [[ "$key" =~ $KEY_RE ]] || fail "invalid key name: '$key'"
      jq_filter+=" | .[\"$key\"] = \$${key}_json"
      jq_args+=(--argjson "${key}_json" "$val")
      ;;
    *=*)
      key="${arg%%=*}"; val="${arg#*=}"
      [[ "$key" =~ $KEY_RE ]] || fail "invalid key name: '$key'"
      jq_filter+=" | .[\"$key\"] = \$${key}_str"
      jq_args+=(--arg "${key}_str" "$val")
      ;;
    *)
      fail "argument '$arg' is not of the form key=val, key:int=val, key:bool=val, or key:json=val"
      ;;
  esac
done

line="$(jq -nc "${jq_args[@]}" "$jq_filter")" || fail "jq failed to construct event JSON"

mkdir -p "$(dirname "$LOG_PATH")" 2>/dev/null || true
echo "$line" >> "$LOG_PATH" || fail "could not append to $LOG_PATH"

# Threshold-based rotation, sf-emit.sh's own default (5000 lines).
if [ -f "$LOG_PATH" ]; then
  lines="$(wc -l < "$LOG_PATH")"
  if [ "$lines" -ge "$ROTATE_THRESHOLD" ]; then
    mkdir -p "$ARCHIVE_DIR" || fail "could not create archive dir $ARCHIVE_DIR for rotation"
    mv "$LOG_PATH" "$ARCHIVE_DIR/PIPELINE_LOG.$(date -u +%Y%m%dT%H%M%SZ).jsonl" || fail "rotation move failed"
    : > "$LOG_PATH"
  fi
fi
```

Every branch that constructs JSON uses `jq --arg`/`--argjson` with the raw value passed as a named variable, never interpolated into the filter string itself — that's what makes an unescaped quote or a stray `"` in a `summary` field inert instead of a JSON-breaking (or injection-class) bug. The key-name regex (`^[a-z][a-z0-9_]*$`) rejects anything that isn't a plain lowercase field name before it ever reaches `jq`.

### The `PreToolUse` guardrail hook

Registered in `.claude/settings.json` the same way the existing `worktree_violation_caught` hook already is:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "scripts/hooks/guard-pipeline-log-writes.sh" }
        ]
      }
    ]
  }
}
```

```bash
#!/usr/bin/env bash
# guard-pipeline-log-writes.sh — PreToolUse hook, matcher: Bash.
# Denies a Bash command that writes to PIPELINE_LOG.jsonl directly, unless
# that command invokes the sanctioned emit-pipeline-event.sh script itself.
# Fails loud: if this hook can't parse its own input, it blocks rather than
# silently letting the tool call through unexamined.
set -euo pipefail

LOG_BASENAME="PIPELINE_LOG.jsonl"          # [CUSTOMIZE]
EMIT_SCRIPT_NAME="emit-pipeline-event.sh"  # [CUSTOMIZE]

input="$(cat)" || { echo '{"decision":"block","reason":"guard-pipeline-log-writes: could not read stdin"}'; exit 0; }
command="$(echo "$input" | jq -r '.tool_input.command // empty')" \
  || { echo '{"decision":"block","reason":"guard-pipeline-log-writes: could not parse tool_input as JSON - failing loud, not open"}'; exit 0; }

[ -n "$command" ] || exit 0   # not a Bash command payload this hook understands; let it through

if echo "$command" | grep -qF "$EMIT_SCRIPT_NAME"; then
  exit 0   # routed through the sanctioned script - allowed
fi

if echo "$command" | grep -qF "$LOG_BASENAME"; then
  echo "{\"decision\":\"block\",\"reason\":\"Direct writes to $LOG_BASENAME are blocked - use scripts/$EMIT_SCRIPT_NAME instead (see Templates/Hooks/README.md). For ad hoc note/incident/decision logging from a free-form session, call the same script directly, e.g.: scripts/$EMIT_SCRIPT_NAME event=note summary='...'\"}"
  exit 0
fi

exit 0
```

[CUSTOMIZE] The exact JSON shape a hook returns (`decision`/`reason` here) must match whatever your project's already-shipped `worktree_violation_caught` hook uses today — copy that contract rather than this doc's, since it's the one already verified working in your `.claude/settings.json`.

## The 14-event schema this was verified against (Argus's own, for illustration), plus 2 added since

[CUSTOMIZE] this table to your own project's schema doc — the first 14 rows are Argus's `docs/PIPELINE_LOG_SCHEMA.md`, reproduced here as the worked example the script's `EVENT_TYPES` allowlist above was checked against line-by-line, not as a universal event vocabulary. `design_exploration_offered`/`design_exploration_declined` are this vault's own later addition (spec.md's STEP 1c, #76 Wave 2) and were never part of Argus's original 14.

| Event | Required fields | Written by |
|---|---|---|
| `bail` | `ts_start`, `ts_end`, `event`, `issue`, `stage` (`pre-dispatch`\|`core-implementer`\|`test-writer`\|`edge-case-auditor`\|`iac-specialist`\|`self-review`), `blocker_type`, `branch`, `summary`, `input_tokens`, `output_tokens`, `token_measurement`, `prior_bail_count`, `recurrence_verdict` (`not_checked`\|`not_recurring`\|`recurring`), `tracking_issue`, `needs_decision_set` | supervisor / spec skill |
| `spec_invoked` | `ts`, `event`, `issue`, `stage`, `blocker_type` | supervisor |
| `pr_opened` | `ts_start`, `ts_end`, `event`, `issue`, `pr`, `branch`, `issue_title`, `model`, `safe_surface`, `specialists`, `doc_updates`, `rebase_count`, `edge_case_rounds`, `input_tokens`, `output_tokens`, `token_measurement` | supervisor |
| `needs_decision` | `ts_start`, `ts_end`, `event`, `issue`, `summary`, `input_tokens`, `output_tokens`, `token_measurement` | spec skill (auto-invoked, non-interactive) |
| `spec_question` | `ts`, `event`, `issue`, `category`, `summary`, `recommendation`, `alternative`, `operator_answer`, `matched_recommendation`, `prior_question_count`, `recurrence_verdict`, `tracking_issue` | spec skill |
| `decision` | `ts`, `event`, `issue`, `category`, `summary`, `recommendation`, `chosen`, `context` | any session acting as supervisor, ad hoc |
| `decision_outcome` | `ts`, `event`, `ref_event` (`spec_question`\|`decision`\|`ecosystem_fix_applied`), `issue`, `category`, `verdict` (`good`\|`bad`\|`mixed`\|`inconclusive`), `confidence` (`high`\|`medium`\|`low`), `evidence`, `note`, `confirmed_by_operator` (`true`) | **pipeline-review's correlation pass only** — never `/implement`/`/spec` |
| `ecosystem_fix_applied` | `ts`, `event`, `issue`, `origin` (`diagnostician_bail`\|`diagnostician_question`\|`manual`), `ref_stage`, `ref_blocker_type`, `ref_category`, `summary`, `closing_pr` | **pipeline-review only** — never by hand |
| `spec_resolved` | `ts_start`, `ts_end`, `event`, `issue`, `blocker_type`, `input_tokens`, `output_tokens`, `token_measurement` | spec skill |
| `spec_completed` | `ts_start`, `ts_end`, `event`, `issue`, `input_tokens`, `output_tokens`, `token_measurement` | spec skill |
| `design_exploration_offered` | `ts`, `event`, `issue`, `summary` | spec skill (STEP 1c, on presenting the 3-way confirm) |
| `design_exploration_declined` | `ts`, `event`, `issue`, `summary` | spec skill (STEP 1c, only when the Operator picks "treat as normal") |
| `requeued` | `ts`, `event`, `issue`, `summary` | supervisor |
| `incident` | `ts`, `event`, `summary` | any session acting as supervisor, ad hoc |
| `note` | `ts`, `event`, `issue?`, `pr?`, `summary` | any session acting as supervisor, ad hoc |
| `worktree_violation_caught` | `ts`, `event`, `caught_by` (`hook`\|`self`), `files`, `summary` | **already mechanized today** — the existing hook, unchanged |

`decision_outcome` and `ecosystem_fix_applied` are the two event types [[Templates/Skills/pipeline-review]]'s own STEP 3b/STEP 3c append — under this guardrail, those appends route through `emit-pipeline-event.sh` exactly like every other event; they are not a separate, exempt write path.

## Related

- [[Principles#Curated judgment and raw telemetry are two different logging problems, not one]] — the design rule this pattern implements
- [[Principles#Guardrails need an anchor outside the agent's own context, not just good prompting]] — why the guardrail lives outside any agent's own context
- [[Principles#Shared shapes need one definition, not one description per reader]]
- [[Templates/Skills/pipeline-review]] — the consumer of this log, and the skill whose STEP 3b/3c appends route through this same mechanism
- [[Templates/CI/README]] — same documented-pattern-with-worked-example shape, applied to a different mechanism
