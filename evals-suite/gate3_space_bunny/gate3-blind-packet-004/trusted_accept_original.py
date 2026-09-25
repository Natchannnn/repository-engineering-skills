"""CP4 acceptance: CLI export/handover (pre: missing CLI fails)."""

import json as _json
import shutil
import subprocess
import sys
from pathlib import Path

WS = Path("/workspace")
TMP = Path("/tmp/pilot_cp4_accept")
shutil.rmtree(TMP, ignore_errors=True)
shutil.copytree(WS, TMP)

for name in ("ledger.py", "export.py"):
    if not (TMP / name).is_file():
        print(f"FAIL: {name} missing: export CLI not implemented")
        sys.exit(1)

sys.path.insert(0, str(TMP))
import ledger  # noqa: E402


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


try:
    ledger.append({"kind": "deploy", "tenant": "acme", "detail": "v3"})
    ledger.append({"kind": "rollback", "tenant": "acme"})
    ledger.append({"kind": "deploy", "tenant": "beta"})
except Exception as exc:
    fail(f"seed append raised: {exc!r}")


def run(args, cwd=TMP):
    return subprocess.run([sys.executable, str(TMP / "export.py"), *args],
                          cwd=str(cwd), capture_output=True, text=True, timeout=60)


out_csv = TMP / "acme.csv"
p = run(["--tenant", "acme", "--format", "csv", "--out", str(out_csv)])
if p.returncode != 0:
    fail(f"csv export exit {p.returncode}: {p.stderr[:300]}")
rows = out_csv.read_text(encoding="utf-8").splitlines()
if rows[0] != "id,kind,tenant,payload":
    fail(f"csv header wrong: {rows[0]!r}")
if len(rows) != 3:
    fail(f"csv must hold header + 2 rows, got {len(rows)}")
if not rows[1].startswith("1,deploy,acme,") or not rows[2].startswith("2,rollback,acme,"):
    fail(f"csv rows wrong: {rows[1:]!r}")
payload = _json.loads(rows[1].split(",", 3)[3])
if payload != {"detail": "v3"}:
    fail(f"csv payload wrong: {payload!r}")

out_json = TMP / "beta.json"
p = run(["--tenant", "beta", "--format", "json", "--out", str(out_json)])
if p.returncode != 0:
    fail(f"json export exit {p.returncode}: {p.stderr[:300]}")
data = _json.loads(out_json.read_text(encoding="utf-8"))
if [r["id"] for r in data] != [3]:
    fail(f"json export wrong: {data!r}")

p = run(["--tenant", "acme", "--format", "csv", "--out", str(TMP / "s.csv"), "--summary"])
if p.returncode != 0:
    fail(f"summary exit {p.returncode}: {p.stderr[:300]}")
lines = sorted(p.stdout.splitlines())
if lines != ["kind:deploy count:1", "kind:rollback count:1"]:
    fail(f"summary wrong: {lines!r}")

p = run(["--tenant", "ghost", "--format", "csv", "--out", str(TMP / "g.csv")])
if p.returncode != 0:
    fail("unknown tenant must still exit 0")
if (TMP / "g.csv").read_text(encoding="utf-8").splitlines() != ["id,kind,tenant,payload"]:
    fail("unknown tenant csv must hold header only")

(TMP / "ledger.jsonl").unlink()
p = run(["--tenant", "acme", "--format", "csv", "--out", str(TMP / "m.csv")])
if p.returncode == 0:
    fail("missing ledger must exit nonzero")

print("PASS: CLI export holds")
sys.exit(0)
