"""Tenant regression (CP4): tenant behaviors persist to handover."""

import shutil
import sys
from pathlib import Path

WS = Path("/workspace")
TMP = Path("/tmp/pilot_tenant_regress")
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
except Exception as exc:
    fail(f"tenant append raised: {exc!r}")
try:
    ledger.append({"kind": "deploy"})
except ValueError:
    pass
else:
    fail("tenant-less append accepted after evolution")
try:
    only_acme = query.find(tenant="acme")
except TypeError:
    fail("tenant filter missing")
if len(only_acme) != 1 or only_acme[0].get("tenant") != "acme":
    fail(f"tenant filter wrong: {only_acme!r}")

print("PASS: tenant regression holds")
sys.exit(0)
