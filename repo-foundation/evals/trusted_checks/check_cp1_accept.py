"""CP1 acceptance: atomic storage works on a fresh copy (pre: missing module fails)."""

import shutil
import sys
from pathlib import Path

WS = Path("/workspace")
TMP = Path("/tmp/pilot_cp1_accept")
shutil.rmtree(TMP, ignore_errors=True)
shutil.copytree(WS, TMP)

mod = TMP / "ledger.py"
if not mod.is_file():
    print("FAIL: ledger.py missing: storage feature not implemented")
    sys.exit(1)

sys.path.insert(0, str(TMP))
import ledger  # noqa: E402


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


try:
    i1 = ledger.append({"kind": "deploy", "detail": "x"})
    i2 = ledger.append({"kind": "rollback"})
    i3 = ledger.append({"kind": "deploy", "tenant": "acme"})
except Exception as exc:
    fail(f"append raised on valid input: {exc!r}")
if (i1, i2, i3) != (1, 2, 3):
    fail(f"ids must be (1, 2, 3), got {(i1, i2, i3)!r}")

lines = (TMP / "ledger.jsonl").read_text(encoding="utf-8").splitlines()
if len(lines) != 3:
    fail(f"ledger.jsonl must hold 3 lines, got {len(lines)}")
import json as _json
recs = [_json.loads(line) for line in lines]
if [r["id"] for r in recs] != [1, 2, 3] or recs[0].get("detail") != "x" or recs[2].get("tenant") != "acme":
    fail(f"records malformed: {recs!r}")

before = (TMP / "ledger.jsonl").read_bytes()
for bad in ({"kind": 123}, {"kind": ""}, {"kind": "  "}, {"nope": 1}, "x", None, [1]):
    try:
        ledger.append(bad)
    except (TypeError, ValueError):
        pass
    else:
        fail(f"append accepted invalid input {bad!r}")
if (TMP / "ledger.jsonl").read_bytes() != before:
    fail("invalid append mutated ledger.jsonl")
if list(TMP.glob("*.tmp")):
    fail("temporary files remain after atomic append")

print("PASS: atomic storage contract holds")
sys.exit(0)
