"""CP4 acceptance v2: parse CSV fields before validating JSON payload."""

import csv as _csv
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
try:
    with out_csv.open("r", encoding="utf-8", newline="") as csv_file:
        rows = list(_csv.reader(csv_file, strict=True))
except _csv.Error as exc:
    fail(f"csv malformed: {exc}")
if not rows or rows[0] != ["id", "kind", "tenant", "payload"]:
    fail(f"csv header wrong: {rows[0] if rows else None!r}")
if len(rows) != 3:
    fail(f"csv must hold header + 2 rows, got {len(rows)}")
if any(len(row) != 4 for row in rows):
    fail(f"csv rows must each have 4 fields: {rows!r}")
if rows[1][:3] != ["1", "deploy", "acme"] or rows[2][:3] != ["2", "rollback", "acme"]:
    fail(f"csv rows wrong: {rows[1:]!r}")
try:
    payload = _json.loads(rows[1][3])
except _json.JSONDecodeError as exc:
    fail(f"csv payload is not JSON: {exc}")
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
with (TMP / "g.csv").open("r", encoding="utf-8", newline="") as csv_file:
    empty_rows = list(_csv.reader(csv_file, strict=True))
if empty_rows != [["id", "kind", "tenant", "payload"]]:
    fail("unknown tenant csv must hold header only")

(TMP / "ledger.jsonl").unlink()
p = run(["--tenant", "acme", "--format", "csv", "--out", str(TMP / "m.csv")])
if p.returncode == 0:
    fail("missing ledger must exit nonzero")

print("PASS: CLI export holds")
sys.exit(0)
