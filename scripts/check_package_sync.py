#!/usr/bin/env python3
"""Check that the shared skills and agents stay in sync across the tool packages.

Every tool package ships its own copy of the same seven step skills and three
orchestration agents. The frontmatter is allowed to differ, because each tool
wires things up its own way: Copilot's agents carry an `mcp-servers` block,
Codex and Antigravity carry the agents as skills and drop `argument-hint`, and
so on. Everything below the frontmatter is the actual instruction set, and it
must be identical everywhere -- otherwise a change lands in one tool and one
tool only, and the packages quietly start behaving differently.

So the rule enforced here is:

  * the body (everything after the frontmatter) must match the canonical copy
    byte for byte
  * every frontmatter key present in *both* files must match -- `name`,
    `description` and `argument-hint` are prompt text, not wiring, and drift in
    them is the same bug as drift in the body
  * a key only one side has is left alone: Copilot's `mcp-servers` block has no
    canonical counterpart, and the variants that deliberately drop
    `argument-hint` keep dropping it

`claude-code` is the canonical copy. Run with --fix to rewrite every variant's
body from it, keeping each variant's own frontmatter.

It also checks that every plugin and marketplace manifest carries the expected
name and that all of them share one version; --fix reports but never edits those.
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

PACKAGES = ["antigravity", "claude-code", "codex", "cursor", "github-copilot", "kiro"]

SHARED_SKILLS = [
    "analyze-codebase",
    "compose-har",
    "fix-and-validate",
    "register-entrypoints",
    "run-scan",
    "setup-auth",
    "setup-repeater",
]

AGENTS = ["bright-application-testing", "bright-discovery", "bright-remediation-loop"]

# Where each agent lives per tool. Codex and Antigravity have no agent concept,
# so they ship the orchestration prompts as skills instead.
AGENT_VARIANTS = [
    "cursor/agents/{agent}.md",
    "antigravity/skills/{agent}/SKILL.md",
    "codex/skills/{agent}/SKILL.md",
    "github-copilot/agents/{agent}.agent.md",
    "github-copilot/.github/agents/{agent}.md",
    "kiro/skills/{agent}/SKILL.md",
]


def split_frontmatter(path: Path) -> tuple[str, str]:
    """Return (frontmatter, body). Frontmatter keeps its delimiters."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise SystemExit(f"{path}: expected YAML frontmatter starting with ---")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise SystemExit(f"{path}: frontmatter is not terminated by ---")
    return text[: end + 5], text[end + 5 :]


def frontmatter_fields(frontmatter: str) -> dict[str, str]:
    """Top-level `key: value` pairs written on a single line.

    Nested blocks such as Copilot's `mcp-servers` yield an empty value, which is
    harmless: they exist on one side only, so they are never compared.
    """
    fields: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if not line or line[0] in " \t#-" or ":" not in line:
            continue
        key, _, value = line.partition(":")
        if key != key.strip():
            continue
        fields[key] = value.strip()
    return fields


def groups() -> list[tuple[str, Path, list[Path]]]:
    """Every (label, canonical, variants) group the check covers."""
    out = []
    for skill in SHARED_SKILLS:
        canonical = REPO / "claude-code" / "skills" / skill / "SKILL.md"
        variants = [
            REPO / pkg / "skills" / skill / "SKILL.md"
            for pkg in PACKAGES
            if pkg != "claude-code"
        ]
        out.append((f"skill {skill}", canonical, variants))
    for agent in AGENTS:
        canonical = REPO / "claude-code" / "agents" / f"{agent}.md"
        variants = [REPO / v.format(agent=agent) for v in AGENT_VARIANTS]
        out.append((f"agent {agent}", canonical, variants))
    return out


def check_orphans(covered: set[Path]) -> list[str]:
    """Flag component files the check does not know about.

    Without this, adding a sixth tool package -- or an eighth skill -- would
    pass CI while being excluded from the very check meant to cover it.
    """
    problems = []
    found: set[Path] = set()
    for pkg_dir in sorted(REPO.glob("*/skills/*/SKILL.md")):
        found.add(pkg_dir)
    for pattern in ("*/agents/*.md", "*/.github/agents/*.md"):
        found.update(REPO.glob(pattern))
    for path in sorted(found - covered):
        problems.append(
            f"{path.relative_to(REPO)}: not covered by the sync check -- "
            f"add it to {Path(__file__).name}"
        )
    return problems


PLUGIN_MANIFESTS = [
    "claude-code/.claude-plugin/plugin.json",
    "cursor/.cursor-plugin/plugin.json",
    "codex/.codex-plugin/plugin.json",
    "github-copilot/plugin.json",
    "antigravity/plugin.json",
    "kiro/plugin.json",
]

MARKETPLACES = [
    ".claude-plugin/marketplace.json",
    ".cursor-plugin/marketplace.json",
    ".github/plugin/marketplace.json",
    ".agents/plugins/marketplace.json",
]


def check_manifests() -> list[str]:
    """Plugin and marketplace manifests agree on names and on one version.

    Each tool reads its own manifest, so a version bumped in one place only
    ships an update to one tool. Nothing here is auto-fixed.
    """
    problems: list[str] = []
    versions: dict[str, str] = {}
    for rel in PLUGIN_MANIFESTS + MARKETPLACES:
        path = REPO / rel
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            problems.append(f"{rel}: cannot read manifest ({exc})")
            continue
        if rel in PLUGIN_MANIFESTS:
            if data.get("name") != "bright-security":
                problems.append(f"{rel}: name is {data.get('name')!r}, expected 'bright-security'")
            versions[rel] = data.get("version")
            continue
        if data.get("name") != "brightsec":
            problems.append(f"{rel}: name is {data.get('name')!r}, expected 'brightsec'")
        plugins = data.get("plugins") or [{}]
        if plugins[0].get("name") != "bright-security":
            problems.append(
                f"{rel}: plugins[0].name is {plugins[0].get('name')!r}, expected 'bright-security'"
            )
        if "version" in data.get("metadata", {}):
            versions[rel] = data["metadata"]["version"]
        elif "version" in plugins[0]:
            versions[rel] = plugins[0]["version"]
    if len(set(versions.values())) > 1:
        listing = "\n".join(f"      {rel}: {ver}" for rel, ver in versions.items())
        problems.append(f"manifest versions differ -- bump them together:\n{listing}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fix",
        action="store_true",
        help="rewrite each variant's body from the canonical copy",
    )
    args = parser.parse_args()

    problems: list[str] = []
    fixed: list[str] = []
    covered: set[Path] = set()

    for label, canonical, variants in groups():
        if not canonical.exists():
            problems.append(f"{label}: canonical copy missing at {canonical.relative_to(REPO)}")
            continue
        covered.add(canonical)
        canon_fm, canon_body = split_frontmatter(canonical)

        for variant in variants:
            covered.add(variant)
            rel = variant.relative_to(REPO)
            if not variant.exists():
                problems.append(f"{label}: missing variant {rel}")
                continue

            var_fm, var_body = split_frontmatter(variant)

            canon_fields = frontmatter_fields(canon_fm)
            var_fields = frontmatter_fields(var_fm)

            for key in canon_fields.keys() & var_fields.keys():
                want, got = canon_fields[key], var_fields[key]
                if want == got:
                    continue
                if args.fix:
                    var_fm = "\n".join(
                        f"{key}: {want}" if line.startswith(f"{key}:") else line
                        for line in var_fm.splitlines()
                    ) + "\n"
                    fixed.append(f"{rel}: frontmatter {key}")
                else:
                    problems.append(
                        f"{rel}: frontmatter `{key}` differs from "
                        f"{canonical.relative_to(REPO)}\n"
                        f"      canonical: {want}\n"
                        f"      variant:   {got}"
                    )

            if var_body != canon_body:
                if args.fix:
                    variant.write_text(var_fm + canon_body, encoding="utf-8")
                    fixed.append(f"{rel}: body")
                else:
                    diff = difflib.unified_diff(
                        canon_body.splitlines(keepends=True),
                        var_body.splitlines(keepends=True),
                        fromfile=str(canonical.relative_to(REPO)),
                        tofile=str(rel),
                    )
                    problems.append(f"{rel}: body differs\n" + "".join(diff).rstrip())
            elif args.fix:
                variant.write_text(var_fm + canon_body, encoding="utf-8")

    unfixable = check_orphans(covered) + check_manifests()
    problems.extend(unfixable)

    if args.fix:
        if fixed:
            print("Synced from claude-code:")
            for item in fixed:
                print(f"  {item}")
        else:
            print("Already in sync; nothing to write.")
        # Orphans and manifest drift cannot be repaired automatically.
        leftovers = unfixable
        for item in leftovers:
            print(f"\n{item}")
        return 1 if leftovers else 0

    if problems:
        print("Packages are out of sync.\n")
        for item in problems:
            print(f"{item}\n")
        print(
            "The tool packages ship the same instructions; a change to one has to reach\n"
            "all of them. Run `python3 scripts/check_package_sync.py --fix` to propagate\n"
            "the canonical claude-code copy, then review the result."
        )
        return 1

    covered_count = len(covered)
    print(f"All {covered_count} skill and agent files are in sync across {len(PACKAGES)} packages.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
