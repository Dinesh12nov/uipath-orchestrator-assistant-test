#!/usr/bin/env python3
"""
Sync the deployed page's content from the uipath-install-upgrade-migration skill.

The page (index.html) embeds the skill's reference guides as a JavaScript `MD`
object. This script finds your NEWEST exported .skill package, reads those guides
straight out of it, and rewrites the `MD = { ... };` block — leaving the rest of
the page (CSS, wizard logic) untouched.

It also copies the newest package into ./skill/ as the canonical record.

Usage:  python3 sync_from_skill.py
"""
import json
import re
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
INDEX = HERE / "index.html"
SKILL_DIRNAME = "uipath-install-upgrade-migration.skill"
CANONICAL_DIR = HERE / "skill"

# Where to look for the newest exported skill package (searched recursively).
SEARCH_ROOTS = [
    Path.home() / "Downloads",
    Path.home() / "Desktop",
    Path.home() / "Documents",
    CANONICAL_DIR,
]

# JS key in the MD object  ->  reference file name inside the skill
MAP = {
    "install":    "standalone-install.md",
    "upgrade":    "standalone-upgrade.md",
    "as":         "automation-suite.md",
    "migration":  "cloud-migration.md",
    "onboarding": "cloud-onboarding.md",
    "folders":    "classic-to-modern-folders.md",
}


def find_newest_skill():
    candidates = []
    for root in SEARCH_ROOTS:
        if root.exists():
            candidates += list(root.rglob(SKILL_DIRNAME))
    if not candidates:
        sys.exit(f"ERROR: no {SKILL_DIRNAME} found under {', '.join(str(r) for r in SEARCH_ROOTS)}")
    newest = max(candidates, key=lambda p: p.stat().st_mtime)
    return newest


def read_reference(zf, filename):
    matches = [n for n in zf.namelist() if n.endswith("references/" + filename)]
    if not matches:
        sys.exit(f"ERROR: {filename} not found inside the skill package")
    return zf.read(matches[0]).decode("utf-8")


def main():
    if not INDEX.exists():
        sys.exit(f"ERROR: index.html not found at {INDEX}")

    skill = find_newest_skill()
    print(f"Using skill package: {skill}")

    with zipfile.ZipFile(skill) as zf:
        content = {key: read_reference(zf, fn) for key, fn in MAP.items()}

    # Keep a canonical copy in the repo.
    CANONICAL_DIR.mkdir(exist_ok=True)
    canonical = CANONICAL_DIR / SKILL_DIRNAME
    if skill.resolve() != canonical.resolve():
        canonical.write_bytes(skill.read_bytes())

    # Build a fresh MD block. json.dumps produces safe, double-quoted JS string
    # literals (newlines/quotes/unicode escaped), matching the original format.
    lines = ["const MD = {"]
    keys = list(MAP.keys())
    for i, key in enumerate(keys):
        literal = json.dumps(content[key])
        comma = "," if i < len(keys) - 1 else ""
        lines.append(f"  {key}: {literal}{comma}")
    lines.append("};")
    new_block = "\n".join(lines)

    html = INDEX.read_text(encoding="utf-8")
    pattern = re.compile(r"const MD = \{.*?\n\};", re.DOTALL)
    if not pattern.search(html):
        sys.exit("ERROR: could not locate the `const MD = { ... };` block in index.html")

    new_html = pattern.sub(lambda m: new_block, html, count=1)

    if new_html == html:
        print("No changes — index.html content already matches the skill.")
        return

    INDEX.write_text(new_html, encoding="utf-8")
    print("Updated index.html MD block from the skill:")
    for key, fn in MAP.items():
        print(f"  MD.{key:<10} <- {fn} ({len(content[key])} chars)")


if __name__ == "__main__":
    main()
