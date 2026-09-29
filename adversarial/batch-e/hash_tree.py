#!/usr/bin/env python3
"""Print a sorted SHA-256 manifest of a directory tree (workspace-integrity helper
for review rounds). Usage: python hash_tree.py <dir>. Files named __pycache__ and
*.pyc are skipped."""
import hashlib
import pathlib
import sys

root = pathlib.Path(sys.argv[1]).resolve()
rows = []
for p in sorted(root.rglob("*")):
    if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc":
        rows.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root).as_posix()}")
print("\n".join(rows))
