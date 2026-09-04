"""One-off scan: find .py modules under app/back/src never imported elsewhere.

ponytail: throwaway script, not part of the shipped codebase. Deleted after use.
"""
from __future__ import annotations

import re
from pathlib import Path

SRC = Path("app/back/src")
SEARCH_ROOTS = [Path("app/back/src"), Path("app/back/tests"), Path("scripts")]

all_files = sorted(SRC.rglob("*.py"))
module_names = {}
for f in all_files:
    rel = f.relative_to(SRC)
    if rel.name == "__init__.py":
        mod = ".".join(rel.parent.parts)
    else:
        mod = ".".join(rel.with_suffix("").parts)
    if mod:
        module_names[mod] = f

# gather all file contents once
all_text = {}
for root in SEARCH_ROOTS:
    for f in root.rglob("*.py"):
        try:
            all_text[f] = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            all_text[f] = f.read_text(encoding="latin-1")

for mod, path in module_names.items():
    if mod.endswith("__init__") or mod == "":
        continue
    last = mod.split(".")[-1]
    pattern = re.compile(rf"(?<![A-Za-z0-9_])({re.escape(mod)}|{re.escape(last)})(?![A-Za-z0-9_])")
    hits = 0
    for f, text in all_text.items():
        if f == path:
            continue
        if pattern.search(text):
            hits += 1
    if hits == 0:
        print(mod, "->", path)
