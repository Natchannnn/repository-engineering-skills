"""Storage regression (CP2+): append keeps working with tenant-bearing events."""

import shutil
import sys
from pathlib import Path

WS = Path("/workspace")
TMP = Path("/tmp/pilot_store_regress")
shutil.rmtree(TMP, ignore_errors=True)
shutil.copytree(WS, TMP)

if not (TMP / "ledger.py").is_file():
    print("FAIL: ledger.py missing")
    sys.exit(1)

sys.path.insert(0, str(TMP))
import ledger  # noqa: E402


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


try:
    a = ledger.append({"kind": "deploy", "tenant": "acme"})
    b = ledger.append({"kind": "scale", "tenant": "beta", "detail": "z"})
except Exception as exc:
    fail(f"append raised: {exc!r}")
if b != a + 1 or a < 1:
    fail(f"ids not sequential: {(a, b)!r}")
recs = ledger.read_all()
got = [r for r in recs if r["id"] in (a, b)]
if len(got) != 2 or got[1].get("detail") != "z" or got[0].get("tenant") != "acme":
    fail(f"appended records malformed: {got!r}")

print("PASS: storage regression holds")
sys.exit(0)
