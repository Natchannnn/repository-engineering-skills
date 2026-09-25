"""CP3 acceptance: tenant contract evolution (pre: old contract fails here)."""

import json as _json
import shutil
import sys
from pathlib import Path

WS = Path("/workspace")
TMP = Path("/tmp/pilot_cp3_accept")
shutil.rmtree(TMP, ignore_errors=True)
shutil.copytree(WS, TMP)

for name in ("ledger.py", "query.py"):
    if not (TMP / name).is_file():
        print(f"FAIL: {name} missing: evolution not implemented")
        sys.exit(1)

sys.path.insert(0, str(TMP))
import ledger  # noqa: E402
import query  # noqa: E402


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


# New contract: tenant required.
before = None
if (TMP / "ledger.jsonl").is_file():
    before = (TMP / "ledger.jsonl").read_bytes()
for bad in ({"kind": "deploy"}, {"kind": "deploy", "tenant": ""},
            {"kind": "deploy", "tenant": "  "}, {"kind": "deploy", "tenant": 7}):
    try:
        ledger.append(dict(bad))
    except ValueError:
        pass
    else:
        fail(f"tenant-less append accepted: {bad!r}")
after = (TMP / "ledger.jsonl").read_bytes() if (TMP / "ledger.jsonl").is_file() else None
if before != after:
    fail("rejected append mutated ledger.jsonl")

try:
    ledger.append({"kind": "deploy", "tenant": "acme"})
    ledger.append({"kind": "scale", "tenant": "beta"})
except Exception as exc:
    fail(f"tenant append raised: {exc!r}")
try:
    got = query.find(tenant="acme")
except TypeError:
    fail("find() lacks the tenant filter (contract not evolved)")
if [r.get("kind") for r in got] != ["deploy"]:
    fail(f"tenant filter wrong: {got!r}")

# Migration of legacy tenant-less records.
LEG = TMP / "legacy.jsonl"
LEG.write_text(
    _json.dumps({"id": 1, "kind": "deploy"}) + "\n"
    + _json.dumps({"id": 2, "kind": "scale", "tenant": "beta"}) + "\n",
    encoding="utf-8",
)
(TMP / "ledger.jsonl").write_bytes(LEG.read_bytes())
try:
    migrated = ledger.migrate()
except AttributeError:
    fail("migrate() missing (contract not evolved)")
except Exception as exc:
    fail(f"migrate() raised: {exc!r}")
recs = [_json.loads(line) for line in (TMP / "ledger.jsonl").read_text(encoding="utf-8").splitlines()]
if migrated != 1 or recs[0].get("tenant") != "default" or recs[1].get("tenant") != "beta":
    fail(f"migrate wrong: count={migrated!r} recs={recs!r}")
if [r["id"] for r in recs] != [1, 2]:
    fail("migrate broke id order")

print("PASS: tenant evolution holds")
sys.exit(0)
