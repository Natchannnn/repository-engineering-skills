"""Comprehensive test suite for CP3_EVOLUTION (Hardcore Enterprise Edition).
Tests all 7 trap dimensions:
1. LEDGER_FILE type contract (literal str)
2. Missing file behavior (None, [], 0, no file creation)
3. Tenant validation (ValueError on missing, empty, blank, non-string)
4. Zero-mutation on rejected appends (byte-exact file comparison)
5. Multi-filter conjunction query (find(kind, tenant)) and backward compatibility
6. Migration mechanics (backfill 'default', count, id order, extra keys)
7. Migration idempotency (second run returns 0, no-op)
"""

import filecmp
import importlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path


def run_checks(ws_path: str):
    ws = Path(ws_path).resolve()
    print(f"\n==========================================")
    print(f"RUNNING CP3 CHECKS ON: {ws}")
    print(f"==========================================")

    tmp_dir = Path(tempfile.mkdtemp(prefix="cp3_check_"))
    try:
        shutil.copytree(ws, tmp_dir / "ws")
        test_ws = tmp_dir / "ws"

        for fname in ["ledger.py", "query.py"]:
            if not (test_ws / fname).exists():
                print(f"FAIL: {fname} missing in workspace")
                return False

        sys.path.insert(0, str(test_ws))
        if "ledger" in sys.modules:
            del sys.modules["ledger"]
        if "query" in sys.modules:
            del sys.modules["query"]

        import ledger
        import query

        score = 0
        total = 25
        details = []

        # -----------------------------------------------------------------
        # TEST 1: LEDGER_FILE Type Contract in query.py (2 pts)
        # -----------------------------------------------------------------
        try:
            if hasattr(query, "LEDGER_FILE") and type(query.LEDGER_FILE) is str:
                score += 2
                details.append("[PASS] Test 1: query.LEDGER_FILE is literal str (2/2)")
            else:
                actual_type = type(getattr(query, "LEDGER_FILE", None))
                details.append(f"[FAIL] Test 1: query.LEDGER_FILE type is {actual_type}, expected literal str (0/2)")
        except Exception as e:
            details.append(f"[FAIL] Test 1: Exception checking LEDGER_FILE: {e} (0/2)")

        # -----------------------------------------------------------------
        # TEST 2: Missing File Handling (4 pts)
        # -----------------------------------------------------------------
        l_file = test_ws / "ledger.jsonl"
        if l_file.exists():
            l_file.unlink()

        t2_pass = True
        try:
            if query.get_by_id(1) is not None:
                t2_pass = False
                details.append("[FAIL] Test 2a: query.get_by_id(1) on missing file != None")
            if query.find() != []:
                t2_pass = False
                details.append("[FAIL] Test 2b: query.find() on missing file != []")
            if query.find("deploy") != []:
                t2_pass = False
                details.append("[FAIL] Test 2c: query.find('deploy') on missing file != []")
            if query.find(tenant="acme") != []:
                t2_pass = False
                details.append("[FAIL] Test 2d: query.find(tenant='acme') on missing file != []")
            if query.find("deploy", tenant="acme") != []:
                t2_pass = False
                details.append("[FAIL] Test 2e: query.find('deploy', tenant='acme') on missing file != []")
            
            if hasattr(ledger, "migrate"):
                mig_missing = ledger.migrate()
                if mig_missing != 0:
                    t2_pass = False
                    details.append(f"[FAIL] Test 2f: ledger.migrate() on missing file returned {mig_missing}, expected 0")
                if l_file.exists():
                    t2_pass = False
                    details.append("[FAIL] Test 2g: ledger.migrate() on missing file created an empty file")
            else:
                t2_pass = False
                details.append("[FAIL] Test 2f: ledger.migrate() missing")
        except Exception as e:
            t2_pass = False
            details.append(f"[FAIL] Test 2: Exception during missing file checks: {e}")

        if t2_pass:
            score += 4
            details.append("[PASS] Test 2: Missing file behavior (query & migrate) (4/4)")
        else:
            details.append("[FAIL] Test 2: Missing file behavior failed some assertions (0/4)")

        # -----------------------------------------------------------------
        # TEST 3: Tenant Validation in append() (4 pts)
        # -----------------------------------------------------------------
        bad_events = [
            {"kind": "deploy"},  # missing tenant
            {"kind": "deploy", "tenant": ""},  # empty string
            {"kind": "deploy", "tenant": "   "},  # whitespace only
            {"kind": "deploy", "tenant": 123},  # int
            {"kind": "deploy", "tenant": None},  # None
            {"kind": "deploy", "tenant": ["acme"]},  # list
        ]
        t3_pass = True
        try:
            for bad in bad_events:
                try:
                    ledger.append(dict(bad))
                    t3_pass = False
                    details.append(f"[FAIL] Test 3: append accepted invalid tenant: {bad}")
                    break
                except ValueError:
                    pass
                except Exception as e:
                    t3_pass = False
                    details.append(f"[FAIL] Test 3: append raised {type(e).__name__} instead of ValueError for {bad}")
                    break
        except Exception as e:
            t3_pass = False
            details.append(f"[FAIL] Test 3: Exception in tenant validation: {e}")

        if t3_pass:
            score += 4
            details.append("[PASS] Test 3: Tenant validation strictly raises ValueError (4/4)")
        else:
            details.append("[FAIL] Test 3: Tenant validation failed (0/4)")

        # -----------------------------------------------------------------
        # TEST 4: Zero Mutation on Rejected Appends (3 pts)
        # -----------------------------------------------------------------
        t4_pass = True
        try:
            id1 = ledger.append({"kind": "init", "tenant": "sys", "env": "prod"})
            before_bytes = l_file.read_bytes()

            for bad in bad_events:
                try:
                    ledger.append(dict(bad))
                except Exception:
                    pass

            after_bytes = l_file.read_bytes()
            if before_bytes != after_bytes:
                t4_pass = False
                details.append("[FAIL] Test 4: Rejected append mutated ledger.jsonl!")
        except Exception as e:
            t4_pass = False
            details.append(f"[FAIL] Test 4: Exception during zero-mutation check: {e}")

        if t4_pass:
            score += 3
            details.append("[PASS] Test 4: Zero mutation on rejected appends byte-exact (3/3)")
        else:
            details.append("[FAIL] Test 4: Zero mutation check failed (0/3)")

        # -----------------------------------------------------------------
        # TEST 5: Conjunction Querying & Backward Compatibility (5 pts)
        # -----------------------------------------------------------------
        t5_pass = True
        try:
            id2 = ledger.append({"kind": "deploy", "tenant": "acme", "ver": "1.0"})
            id3 = ledger.append({"kind": "deploy", "tenant": "beta", "ver": "1.1"})
            id4 = ledger.append({"kind": "scale", "tenant": "acme", "count": 5})

            if [r["id"] for r in query.find()] != [1, 2, 3, 4]:
                t5_pass = False
                details.append(f"[FAIL] Test 5a: find() returned {[r['id'] for r in query.find()]}, expected [1, 2, 3, 4]")
            if [r["id"] for r in query.find("deploy")] != [2, 3]:
                t5_pass = False
                details.append(f"[FAIL] Test 5b: find('deploy') positional backward compat failed: {[r['id'] for r in query.find('deploy')]}")
            if [r["id"] for r in query.find(tenant="acme")] != [2, 4]:
                t5_pass = False
                details.append(f"[FAIL] Test 5c: find(tenant='acme') failed: {[r['id'] for r in query.find(tenant='acme')]}")
            if [r["id"] for r in query.find("deploy", tenant="acme")] != [2]:
                t5_pass = False
                details.append(f"[FAIL] Test 5d: find('deploy', tenant='acme') conjunction failed: {[r['id'] for r in query.find('deploy', tenant='acme')]}")
            if query.find("scale", tenant="beta") != []:
                t5_pass = False
                details.append(f"[FAIL] Test 5e: find('scale', tenant='beta') non-match failed")
            rec = query.get_by_id(2)
            if not rec or rec.get("kind") != "deploy" or rec.get("tenant") != "acme" or rec.get("ver") != "1.0":
                t5_pass = False
                details.append(f"[FAIL] Test 5f: get_by_id(2) failed or lost fields: {rec}")
        except Exception as e:
            t5_pass = False
            details.append(f"[FAIL] Test 5: Exception during conjunction query checks: {e}")

        if t5_pass:
            score += 5
            details.append("[PASS] Test 5: Conjunction querying and backward compatibility (5/5)")
        else:
            details.append("[FAIL] Test 5: Conjunction querying failed (0/5)")

        # -----------------------------------------------------------------
        # TEST 6: Migration Mechanics (4 pts)
        # -----------------------------------------------------------------
        t6_pass = True
        try:
            legacy_data = [
                {"id": 1, "kind": "bootstrap"},                          # missing tenant
                {"id": 2, "kind": "deploy", "tenant": "acme"},           # valid tenant
                {"id": 3, "kind": "metric", "tenant": ""},               # empty tenant
                {"id": 4, "kind": "audit", "tenant": "   "},             # whitespace tenant
                {"id": 5, "kind": "auth", "tenant": 999},                # non-string tenant
                {"id": 6, "kind": "cleanup", "tenant": "default"},        # already default
            ]
            with open(l_file, "w", encoding="utf-8") as f:
                for r in legacy_data:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")

            if hasattr(ledger, "migrate"):
                migrated_count = ledger.migrate()
                recs = [json.loads(line) for line in l_file.read_text(encoding="utf-8").splitlines() if line.strip()]

                if migrated_count != 4:
                    t6_pass = False
                    details.append(f"[FAIL] Test 6a: migrate() returned {migrated_count}, expected 4")
                if len(recs) != 6:
                    t6_pass = False
                    details.append(f"[FAIL] Test 6b: migrate() resulted in {len(recs)} records, expected 6")
                if [r["id"] for r in recs] != [1, 2, 3, 4, 5, 6]:
                    t6_pass = False
                    details.append(f"[FAIL] Test 6c: migrate() broke id ordering: {[r['id'] for r in recs]}")
                if recs[0].get("tenant") != "default" or recs[0].get("kind") != "bootstrap":
                    t6_pass = False
                    details.append(f"[FAIL] Test 6d: rec 1 not backfilled: {recs[0]}")
                if recs[1].get("tenant") != "acme":
                    t6_pass = False
                    details.append(f"[FAIL] Test 6e: rec 2 tenant overwritten: {recs[1]}")
                if recs[2].get("tenant") != "default":
                    t6_pass = False
                    details.append(f"[FAIL] Test 6f: rec 3 empty tenant not backfilled: {recs[2]}")
                if recs[3].get("tenant") != "default":
                    t6_pass = False
                    details.append(f"[FAIL] Test 6g: rec 4 whitespace tenant not backfilled: {recs[3]}")
                if recs[4].get("tenant") != "default":
                    t6_pass = False
                    details.append(f"[FAIL] Test 6h: rec 5 non-str tenant not backfilled: {recs[4]}")
                if recs[5].get("tenant") != "default":
                    t6_pass = False
                    details.append(f"[FAIL] Test 6i: rec 6 default tenant altered: {recs[5]}")
            else:
                t6_pass = False
                details.append("[FAIL] Test 6: ledger.migrate() missing")
        except Exception as e:
            t6_pass = False
            details.append(f"[FAIL] Test 6: Exception during migration checks: {e}")

        if t6_pass:
            score += 4
            details.append("[PASS] Test 6: Migration mechanics & backfill integrity (4/4)")
        else:
            details.append("[FAIL] Test 6: Migration mechanics failed (0/4)")

        # -----------------------------------------------------------------
        # TEST 7: Migration Idempotency (3 pts)
        # -----------------------------------------------------------------
        t7_pass = True
        try:
            if hasattr(ledger, "migrate"):
                content_after_first = l_file.read_bytes()
                second_mig = ledger.migrate()
                content_after_second = l_file.read_bytes()

                if second_mig != 0:
                    t7_pass = False
                    details.append(f"[FAIL] Test 7a: second migrate() returned {second_mig}, expected 0")
                if content_after_first != content_after_second:
                    t7_pass = False
                    details.append("[FAIL] Test 7b: second migrate() modified already-migrated file")
            else:
                t7_pass = False
                details.append("[FAIL] Test 7: ledger.migrate() missing")
        except Exception as e:
            t7_pass = False
            details.append(f"[FAIL] Test 7: Exception during idempotency check: {e}")

        if t7_pass:
            score += 3
            details.append("[PASS] Test 7: Migration idempotency (3/3)")
        else:
            details.append("[FAIL] Test 7: Migration idempotency failed (0/3)")

        # -----------------------------------------------------------------
        # FINAL SCORE REPORT
        # -----------------------------------------------------------------
        print("\n--- RESULTS ---")
        for d in details:
            print(d)
        print(f"\nFINAL VERDICT: {score}/{total} ({'FULL PASS' if score == total else 'FAILED'})")
        return score == total

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_cp3.py <workspace_dir>")
        sys.exit(1)
    success = run_checks(sys.argv[1])
    sys.exit(0 if success else 1)
