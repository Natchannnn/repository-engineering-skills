"""Query regression (CP3+): kind queries keep working across the tenant evolution."""

import shutil
import sys
from pathlib import Path

WS = Path("/workspace")
TMP = Path("/tmp/pilot_query_regress")
shutil.rmtree(TMP, ignore_errors=True)
shutil.copytree(WS, TMP)

for name in ("ledger.py", "query.py"):
    if not (TMP / name).is_file():
        print(f"FAIL: {name} missing")
        sys.exit(1)

sys.path.insert(0, str(TMP))
import ledger  # noqa: E402
import query  # noqa: E402


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


try:
    ledger.append({"kind": "deploy", "tenant": "acme"})
    ledger.append({"kind": "scale", "tenant": "beta"})
except Exception as exc:
    fail(f"seed append raised: {exc!r}")
if query.get_by_id(1).get("kind") != "deploy":
    fail("get_by_id broken after evolution")
if [r["id"] for r in query.find(kind="deploy")] != [1]:
    fail("kind-only find broken after evolution")

print("PASS: query regression holds")
sys.exit(0)
