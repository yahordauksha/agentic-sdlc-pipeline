#!/usr/bin/env python3
"""Structural lint for this vault: every [[wiki-link]] must resolve to a real
file (and header, if given), every Templates/Agents+Skills file must have
its required frontmatter fields, every Templates/Agents+Skills and
.claude/agents+commands file must keep its frontmatter `version:` and body
`> Version X` line in sync, and the tip commit must reference an issue
number if it touches a load-bearing vault file. Stdlib only - no dependencies
to install in CI.
"""
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
EXCLUDE_DIRS = {".git", ".obsidian", "node_modules"}

WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
FENCE_RE = re.compile(r"^\s*```")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
ISSUE_REF_RE = re.compile(r"#\d+")

AGENT_REQUIRED_FIELDS = ["name", "description", "tools", "model", "version"]
SKILL_REQUIRED_FIELDS = ["allowed-tools", "description", "model", "version"]
# .claude/agents and .claude/commands are this vault's own live copies, not
# templates - they don't share Templates/*'s full required-field shape (e.g.
# not every vault-only skill declares `model`), but per #61 they do carry a
# `version` field now, so that much is enforced the same way.
VAULT_LIVE_REQUIRED_FIELDS = ["version"]

VERSION_FIELD_RE = re.compile(r"^version:\s*(\S+)")
BODY_VERSION_RE = re.compile(r"^>\s*Version\s+(\S+)\s*$")

# Paths where an edit needs a paper trail (an issue number in the commit
# message) - shape.md's own close-out convention, enforced instead of assumed.
LOAD_BEARING_PATTERNS = [
    "Templates/Agents/*.md",
    "Templates/Skills/*.md",
    ".claude/commands/*.md",
    "Principles.md",
    "Home.md",
    "Timeline.md",
]


def all_markdown_files():
    for path in ROOT.rglob("*.md"):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        yield path


def strip_code_fences(lines):
    """Return lines with fenced code-block contents blanked out (line count preserved)."""
    out = []
    in_fence = False
    for line in lines:
        if FENCE_RE.match(line):
            in_fence = not in_fence
            out.append("")
            continue
        out.append("" if in_fence else line)
    return out


def normalize_heading(text):
    text = re.sub(r"[`*_]", "", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def build_index(files):
    """path_key (relative posix path w/o .md) -> Path, and basename -> [Path,...]."""
    by_path = {}
    by_basename = {}
    headings_by_file = {}
    for f in files:
        rel = f.relative_to(ROOT).with_suffix("")
        by_path[rel.as_posix()] = f
        by_basename.setdefault(rel.name, []).append(f)

        lines = f.read_text(encoding="utf-8").splitlines()
        headings = set()
        for line in strip_code_fences(lines):
            m = HEADING_RE.match(line)
            if m:
                headings.add(normalize_heading(m.group(2)))
        headings_by_file[f] = headings
    return by_path, by_basename, headings_by_file


def resolve_link(link_path, by_path, by_basename):
    """Return (resolved_file_or_None, error_message_or_None). A link to an
    existing directory (e.g. [[Templates/Agents]] as a category reference,
    not a specific file) resolves with no file to check headings against."""
    if link_path in by_path:
        return by_path[link_path], None
    if (ROOT / link_path).is_dir():
        return "DIR", None
    basename = link_path.rsplit("/", 1)[-1]
    candidates = by_basename.get(basename, [])
    if len(candidates) == 1:
        return candidates[0], None
    if len(candidates) > 1:
        return None, f"ambiguous target ({len(candidates)} files named {basename!r})"
    return None, "no matching file"


def check_wikilinks(files, by_path, by_basename, headings_by_file):
    errors = []
    for f in files:
        lines = f.read_text(encoding="utf-8").splitlines()
        for lineno, line in enumerate(strip_code_fences(lines), start=1):
            line = INLINE_CODE_RE.sub("", line)
            for raw in WIKILINK_RE.findall(line):
                target = raw.split("|", 1)[0].strip()
                if "#" in target:
                    link_path, heading = target.split("#", 1)
                else:
                    link_path, heading = target, None
                link_path = link_path.strip()
                if not link_path:
                    continue
                resolved, err = resolve_link(link_path, by_path, by_basename)
                rel_f = f.relative_to(ROOT)
                if err:
                    errors.append(f"{rel_f}:{lineno}: [[{raw}]] -> {err}")
                    continue
                if resolved == "DIR":
                    if heading:
                        errors.append(
                            f"{rel_f}:{lineno}: [[{raw}]] -> "
                            f"'{link_path}' is a directory, can't have a heading fragment"
                        )
                    continue
                if heading:
                    wanted = normalize_heading(heading)
                    if wanted not in headings_by_file[resolved]:
                        errors.append(
                            f"{rel_f}:{lineno}: [[{raw}]] -> "
                            f"no heading matching '{heading}' in {resolved.relative_to(ROOT)}"
                        )
    return errors


def frontmatter_block(f):
    lines = f.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[1:i]
    return None


def check_frontmatter(pattern_dir, required_fields):
    errors = []
    for f in sorted((ROOT / pattern_dir).glob("*.md")):
        block = frontmatter_block(f)
        rel_f = f.relative_to(ROOT)
        if block is None:
            errors.append(f"{rel_f}: missing frontmatter block")
            continue
        for field in required_fields:
            pat = re.compile(rf"^{re.escape(field)}:\s*\S")
            if not any(pat.match(line) for line in block):
                errors.append(f"{rel_f}: missing required frontmatter field '{field}'")
    return errors


def check_version_sync(pattern_dir):
    """The frontmatter `version:` field and the body's `> Version X` line
    (added right after the frontmatter closes) must always agree - two
    copies of the same fact drift apart unless something checks them."""
    errors = []
    for f in sorted((ROOT / pattern_dir).glob("*.md")):
        rel_f = f.relative_to(ROOT)
        lines = f.read_text(encoding="utf-8").splitlines()
        block = frontmatter_block(f)
        if block is None:
            continue  # already reported by check_frontmatter
        fm_version = None
        for line in block:
            m = VERSION_FIELD_RE.match(line)
            if m:
                fm_version = m.group(1)
                break
        if fm_version is None:
            continue  # already reported by check_frontmatter

        body_start = len(block) + 2  # frontmatter lines + both '---' fences
        body_version = None
        for line in lines[body_start:]:
            if line.strip() == "":
                continue
            m = BODY_VERSION_RE.match(line)
            if m:
                body_version = m.group(1)
            break
        if body_version is None:
            errors.append(f"{rel_f}: missing '> Version {fm_version}' body line after frontmatter")
        elif body_version != fm_version:
            errors.append(
                f"{rel_f}: frontmatter version '{fm_version}' != body version line '{body_version}'"
            )
    return errors


def is_load_bearing(rel_path):
    return any(PurePosixPath(rel_path).match(pattern) for pattern in LOAD_BEARING_PATTERNS)


def check_commit_paper_trail():
    """The tip commit's message must reference an issue (#<n>) if it touches
    a load-bearing vault file. Skips (with a warning, not a failure) if the
    commit's parent isn't available locally, e.g. a shallow clone - can't
    tell truthfully in that case, so it doesn't claim a false pass or fail."""
    try:
        changed = subprocess.run(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.splitlines()
        message = subprocess.run(
            ["git", "log", "-1", "--format=%B", "HEAD"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout
    except subprocess.CalledProcessError:
        print("vault-lint: WARNING - could not inspect HEAD's diff (shallow clone or no parent); skipping commit paper-trail check")
        return []

    touched = sorted(p for p in changed if is_load_bearing(p))
    if touched and not ISSUE_REF_RE.search(message):
        files_list = ", ".join(touched)
        return [
            f"HEAD commit touches load-bearing file(s) ({files_list}) but its "
            f"message has no issue reference (e.g. '#40') - see shape.md's close-out step"
        ]
    return []


def main():
    files = list(all_markdown_files())
    by_path, by_basename, headings_by_file = build_index(files)

    errors = []
    errors += check_wikilinks(files, by_path, by_basename, headings_by_file)
    errors += check_frontmatter("Templates/Agents", AGENT_REQUIRED_FIELDS)
    errors += check_frontmatter("Templates/Skills", SKILL_REQUIRED_FIELDS)
    errors += check_frontmatter(".claude/agents", VAULT_LIVE_REQUIRED_FIELDS)
    errors += check_frontmatter(".claude/commands", VAULT_LIVE_REQUIRED_FIELDS)
    errors += check_version_sync("Templates/Agents")
    errors += check_version_sync("Templates/Skills")
    errors += check_version_sync(".claude/agents")
    errors += check_version_sync(".claude/commands")
    errors += check_commit_paper_trail()

    if errors:
        print(f"vault-lint: {len(errors)} problem(s) found\n")
        for e in errors:
            print(f"  {e}")
        return 1

    print(f"vault-lint: OK ({len(files)} files checked, all wiki-links and frontmatter valid)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
