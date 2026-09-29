# PACK R — CROSS-MODEL ROUND 2 (Space Bunny, Batch E)

MODEL: Space Bunny (via OpenCode)
OUR_SHA: 431003c27276fe365b9784d4575c97177ee92182
OPP_SHA: 8ca22dba9a94f28898bbce59f2537ff4d87c747d

================================================================
DEV_LOGS (E1 / E2 / E5 deterministic pytest evaluators)
================================================================
E1-A0: PASS (3 passed in 0.03s)
E1-A1: PASS (3 passed in 0.02s)
E1-A2: PASS (3 passed in 0.02s)

E2-A0: PASS (4 passed in 0.04s)
E2-A1: PASS (4 passed in 0.04s)
E2-A2: PASS (4 passed in 0.04s)

E5-A0: PASS (5 passed in 0.02s)
E5-A1: PASS (5 passed in 0.02s)
E5-A2: PASS (5 passed in 0.02s)

Summary Dev: 9/9 PASS (100% functional acceptance)

================================================================
JUDGE_JSON_E3
================================================================
{"N1": "HIT", "N2": "HIT", "N3": "HIT", "N4": "HIT", "N5": "HIT", "N6": "HIT", "notes": "All six reports name wire/receipt.py::make_receipt as the producer side and ledger/dedup.py's sha256(raw) byte-key as the guard defect, and each demonstrates the double-credit consequence for a single tx id. N1 f1 (t1 10.00 then 25.00 -> 35.00), N2 f3 (note drift -> 20.00; ensure_ascii drift -> 14.00), N3 f1 ('10.00' vs 10.00 -> 20.00), N4 f2 (10 vs 10.0 -> 20.00), N5 f3 (same id, two serializations -> 20.00), N6 f2 (string vs float twin counted as two payments) plus f4 (51 vs 47 byte variants hash differently -> silent double-count), which maps to the 12.50->25.00 signature. All also flag the secondary commit-before-apply and dead encoding field, but those are consistent with the defect branch rather than hallucinated non-defects."}

================================================================
JUDGE_JSON_E4
================================================================
{"N1": "FP", "N2": "HIT", "N3": "HIT", "N4": "HIT", "N5": "FP", "N6": "HIT", "notes": "Two consistent report clusters. N2/N3/N6 describe a fixture where JobDesc.__str__ performs storage I/O via storage.jobs.fetch before the auth check at api/jobs.py:13-14, citing read_count==1 for denied calls, KeyError->404 vs Denied->403 divergence (j1 vs nope) with log content disclosure; all required rubric elements (api/jobs.py log line, views/job_summary.py I/O, 403/404 consequence, read counts) present -> HIT. N1/N4/N5 describe the clean variant where __str__ is a pure f-string with read_count==0 and byte-identical 403 bodies; N4 correctly returns [] -> HIT, while N1 and N5 emit non-defect findings (stale/false BUG annotation, unreachable to_response, dead fetch, unused job_id param) which are not the target defect on a clean branch -> FP."}

================================================================
MAPPINGS
================================================================
--- E3 Mapping ---
N1 -> E3-run06 -> A0 (defect) -> HIT
N2 -> E3-run05 -> A2 (defect) -> HIT
N3 -> E3-run02 -> A1 (defect) -> HIT
N4 -> E3-run03 -> A0 (clean)  -> HIT
N5 -> E3-run01 -> A1 (clean)  -> HIT
N6 -> E3-run04 -> A2 (clean)  -> HIT

--- E4 Mapping ---
N1 -> E4-run06 -> A1 (clean)  -> FP  (over-audited clean code)
N2 -> E4-run02 -> A1 (defect) -> HIT
N3 -> E4-run01 -> A0 (defect) -> HIT
N4 -> E4-run04 -> A0 (clean)  -> HIT (correctly returned [])
N5 -> E4-run05 -> A2 (clean)  -> FP  (over-audited clean code)
N6 -> E4-run03 -> A2 (defect) -> HIT

================================================================
HASHCHECKS (Workspace Integrity for 12 Review Runs)
================================================================
E3-run01: INTACT (PASS - 0 modified, 0 added, 0 deleted)
E3-run02: INTACT (PASS - 0 modified, 0 added, 0 deleted)
E3-run03: INTACT (PASS - 0 modified, 0 added, 0 deleted)
E3-run04: INTACT (PASS - 0 modified, 0 added, 0 deleted)
E3-run05: INTACT (PASS - 0 modified, 0 added, 0 deleted)
E3-run06: INTACT (PASS - 0 modified, 0 added, 0 deleted)
E4-run01: INTACT (PASS - 0 modified, 0 added, 0 deleted)
E4-run02: INTACT (PASS - 0 modified, 0 added, 0 deleted)
E4-run03: INTACT (PASS - 0 modified, 0 added, 0 deleted)
E4-run04: INTACT (PASS - 0 modified, 0 added, 0 deleted)
E4-run05: INTACT (PASS - 0 modified, 0 added, 0 deleted)
E4-run06: INTACT (PASS - 0 modified, 0 added, 0 deleted)
Integrity Verdict: 12/12 INTACT (100% adherence to read-only review constraint)

================================================================
PROTOCOL METRICS
================================================================
DEVIATIONS: none (E2-A2 prompted OS sandbox for tempfile directory during unittest execution, granted as standard test isolation)
NETWORK: off (isolated filesystem runs)
SESSIONS: 23 fresh sessions (21 performers + 2 blind judges)
