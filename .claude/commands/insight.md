---
allowed-tools: Bash(ls:*), Bash(stat:*), Bash(date:*), Read, Write
description: Archive today's built-in /insights report into this vault, with a personalized "Nice to Learn" section grounded in your actual session data.
version: 1.0.0
---

> Version 1.0.0

You are archiving today's Claude Code `/insights` report into this vault's `Insights/` folder, and extending it with a personalized "Nice to Learn" section. You do not regenerate the underlying analysis — only the built-in `/insights` command can do that.

## Step 1 — Check freshness

Check the modification time of `~/.claude/usage-data/report.html`. If it doesn't exist, or wasn't modified today, tell the user to run the built-in `/insights` command first, then stop — do not proceed on stale data.

## Step 2 — Read the report and the underlying facet data

Read `~/.claude/usage-data/report.html` in full — this HTML is the base of the archived file and must not be altered.

Read the JSON files in `~/.claude/usage-data/facets/` (one per session: `goal_categories`, `outcomes`, `user_satisfaction_counts`, `friction_counts`). This is what grounds the "Nice to Learn" section in real evidence instead of generic advice.

## Step 3 — Write the "Nice to Learn" section

Produce 3–5 recommendations, fewer if the evidence doesn't support more. Each one must:

- Name the specific pattern that prompted it, citing actual counts/frequency from the facet data (e.g. "context/compaction friction showed up in 4 of your last 7 sessions").
- Name the underlying knowledge gap that pattern points to.
- Recommend one or two specific, real resources — prefer official Claude Code docs (`code.claude.com/docs/...`) or well-established, widely-known references. Never invent or guess a URL you aren't confident exists.

Do not include filler recommendations ("learn more about X") that aren't tied to an observed pattern in the facet data.

Format the section as HTML, reusing the report's own CSS classes (e.g. `.key-insight`) so it reads as native to the document rather than bolted on.

## Step 4 — Combine and save

Insert the new section immediately before `</body>` in the report HTML. Get today's date (`date +%Y-%m-%d`) and write the combined file to `Insights/<YYYY-MM-DD>.html` in this vault, matching the naming convention already used there.

## Step 5 — Confirm

Tell the user the file was saved, and give a one-line summary of what the "Nice to Learn" section covered.
