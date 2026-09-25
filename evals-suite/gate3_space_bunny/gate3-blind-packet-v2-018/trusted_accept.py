"""CP2 acceptance: query pipeline on a seeded copy (pre: missing module fails)."""

import shutil
import sys
from pathlib import Path

WS = Path("/workspace")
TMP = Path("/tmp/pilot_cp2_accept")
shutil.rmtree(TMP, ignore_errors=True)
shutil.copytree(WS, TMP)

for name in ("ledger.py", "query.py"):
    if not (TMP / name).is_file():
        print(f"FAIL: {name} missing: query pipeline not implemented")
        sys.exit(1)

sys.path.insert(0, str(TMP))
import ledger  # noqa: E402
import query  # noqa: E402


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


try:
    ledger.append({"kind": "deploy", "tenant": "acme"})
    ledger.append({"kind": "rollback", "tenant": "acme"})
    ledger.append({"kind": "deploy", "tenant": "beta"})
except Exception as exc:
    fail(f"seed append raised: {exc!r}")

r2 = query.get_by_id(2)
if not isinstance(r2, dict) or r2.get("kind") != "rollback":
    fail(f"get_by_id(2) wrong: {r2!r}")
if query.get_by_id(99) is not None:
    fail("get_by_id(99) must be None")
deps = query.find(kind="deploy")
if [r["id"] for r in deps] != [1, 3]:
    fail(f"find(kind='deploy') wrong: {deps!r}")
if len(query.find()) != 3:
    fail("find() must return all records")

# Missing ledger behavior on an empty dir.
EMPTY = TMP / "empty_probe"
EMPTY.mkdir(exist_ok=True)
for name in ("ledger.py", "query.py"):
    shutil.copy2(TMP / name, EMPTY / name)
sys.path.insert(0, str(EMPTY))
import importlib.util as _ilu

spec_l = _ilu.spec_from_file_location("ledger_empty", EMPTY / "ledger.py")
ledger_empty = _ilu.module_from_spec(spec_l)
spec_l.loader.exec_module(ledger_empty)
spec_q = _ilu.spec_from_file_location("query_empty", EMPTY / "query.py")
query_empty = _ilu.module_from_spec(spec_q)
spec_q.loader.exec_module(query_empty)
import os as _os

_old = _os.getcwd()
try:
    _os.chdir(EMPTY)
    if query_empty.get_by_id(1) is not None or query_empty.find() != []:
        fail("missing ledger must yield None/[]")
finally:
    _os.chdir(_old)

print("PASS: query pipeline holds")
sys.exit(0)
