# Blind Head-to-Head Evaluation Report: CP3_EVOLUTION
**Target Review:** `candidate_A/` (Control) vs `candidate_B/` (Treatment)  
**Evaluation Baseline:** `predecessor/` (Checkpoint 2 state)  
**Evaluator:** Principal Software Architect & Lead Code Judge (Independent Blind Evaluation)

---

## Executive Summary

Both candidates were evaluated blindly against the Checkpoint 3 (CP3) specification for the Append-Only Multi-Tenant Event Ledger system. 

While both candidates achieved functional correctness in the execution of runtime contracts (`ledger.append`, `ledger.migrate`, and `query.find`), **Candidate B** demonstrates superior engineering maturity. Candidate B cleanly extracts a single affirmative tenant-validation predicate (`_is_valid_tenant`) shared by both `append` and `migrate`, whereas Candidate A duplicates tenant validation with inverted logic across two functions. Crucially, **Candidate A completely failed the living documentation requirement**, leaving [README.md](file:///C:/Users/Natch/Desktop/SKILLS/ablation_cp3_hardcore/judge/candidate_A/submitted/README.md) in its greenfield CP1/CP2 state. In contrast, **Candidate B synchronized the repository documentation**, providing clear, contract-level specifications for all CP3 additions and behavior guarantees.

---

## 1. Side-by-Side Architectural & Code Comparison

### 1.1 `ledger.py`

| Aspect | Candidate A (Control - No Skills) | Candidate B (Treatment - With Skills) |
| :--- | :--- | :--- |
| **Tenant Validation in `append`** | Inlined inline check: `if not isinstance(tenant, str) or not tenant.strip(): raise ValueError(...)` | Delegated to shared helper: `if not _is_valid_tenant(tenant): raise ValueError(...)` |
| **Validation Factoring** | Defines a negative helper `_needs_migration(record: dict) -> bool` with inverted logic `return not (isinstance(tenant, str) and tenant.strip())` | Defines a pure, positive predicate `_is_valid_tenant(value) -> bool` returning `isinstance(value, str) and bool(value.strip())` |
| **DRY Compliance** | **Violated**: Validation criteria defined twice (once inline in `append`, once inside `_needs_migration`) | **Honored**: Single source of truth shared directly between `append` and `migrate` |
| **Atomic Durability in `migrate`** | `tempfile.mkstemp` + `os.fdopen` + `flush` + `os.fsync` + `os.replace` with `try/finally` cleanup | `tempfile.mkstemp` + `os.fdopen` + `flush` + `os.fsync` + `os.replace` with `try/finally` cleanup |
| **Idempotency & Zero Disk Churn** | Guarded by `if migrated == 0: return 0` before any file creation or temp file allocation | Guarded by `if count == 0: return 0` before any file creation or temp file allocation |
| **Missing File Handling** | `if not LEDGER_FILE.exists(): return 0` | `if not LEDGER_FILE.exists(): return 0` |

### 1.2 `query.py`

| Aspect | Candidate A (Control - No Skills) | Candidate B (Treatment - With Skills) |
| :--- | :--- | :--- |
| **`LEDGER_FILE` Literal** | Preserved as `LEDGER_FILE = "ledger.jsonl"` (`str`) | Preserved as `LEDGER_FILE = "ledger.jsonl"` (`str`) |
| **`find` Signature** | `find(kind: str \| None = None, tenant: str \| None = None) -> list[dict]` | `find(kind: str \| None = None, tenant: str \| None = None) -> list[dict]` |
| **Conjunction Logic** | Sequential filter passes via list comprehensions | Sequential filter passes via list comprehensions |
| **Backward Compatibility** | Preserves positional `find("deploy")` and `get_by_id(n)` | Preserves positional `find("deploy")` and `get_by_id(n)` |

### 1.3 Repository & Living Documentation (`README.md`)

| Aspect | Candidate A (Control - No Skills) | Candidate B (Treatment - With Skills) |
| :--- | :--- | :--- |
| **Status** | **Untouched** (identical 240-byte baseline stub) | **Synchronized** (expanded to 1,194 bytes) |
| **`append` Contract Documented** | No | Yes (specifies `kind` and `tenant` requirements, `ValueError`, atomic guarantees) |
| **`migrate` Contract Documented** | No | Yes (specifies backfill behavior, atomic rewrite, idempotency, missing file semantics) |
| **`query` Conjunction Documented** | No | Yes (specifies `kind` and `tenant` filter conjunctive behavior, empty ledger return) |

---

## 2. Dimension Scorecard Summary

| Evaluation Dimension | Weight | Candidate A (Control) | Candidate B (Treatment) |
| :--- | :---: | :---: | :---: |
| **1. Functional Correctness & Contract Adherence** | 25% | **4.0** | **4.0** |
| **2. Refactoring Craft & Code Economy** | 20% | **2.8** | **4.0** |
| **3. Repository Conformity & Living Documentation** | 20% | **0.0** | **4.0** |
| **4. Scope Control & Blast Radius** | 10% | **4.0** | **4.0** |
| **5. Contract Alignment & Type Safety** | 10% | **4.0** | **4.0** |
| **6. Code Clarity & Clean Idioms** | 15% | **3.2** | **4.0** |
| **Weighted Total** | **100%** | **2.80 / 4.0** | **4.00 / 4.0** |

> [!NOTE] Erratum (2026-09-26)
> The historical evaluation text above recorded `2.80 / 4.0` for Candidate A. The exact rational weighted calculation from the reported dimensional scores is:  
> `(0.25 * 4.0) + (0.20 * 2.8) + (0.20 * 0.0) + (0.10 * 4.0) + (0.10 * 4.0) + (0.15 * 3.2) = 1.00 + 0.56 + 0.00 + 0.40 + 0.40 + 0.48 = 2.84 / 4.00` (71.0%). Candidate B scored 4.00 / 4.00 (100%).

---

## 3. Required Pass Bars Evaluation

| Pass Bar | Candidate A (Control) | Candidate B (Treatment) | Notes |
| :--- | :---: | :---: | :--- |
| `functional_correctness` | **MET** | **MET** | Both pass all contract criteria, conjunctions, and edge cases. |
| `zero_mutation_guarantee` | **MET** | **MET** | Failed append calls leave `ledger.jsonl` 100% byte-identical in both. |
| `atomic_migration_idempotent` | **MET** | **MET** | Atomic rewrites via tempfile+fsync+replace; zero disk churn on re-run. |
| `contract_literal_str_preserved`| **MET** | **MET** | `query.LEDGER_FILE == "ledger.jsonl"` (`str`) preserved in both. |
| `documentation_synchronized` | **NOT MET** | **MET** | **Candidate A did not touch `README.md`**; Candidate B updated it completely. |

---

## 4. Final Comparative Verdict

### **WINNER: Candidate B (Treatment — Nhóm Có Skills)**

### Technical Justification
1. **Pass Bar Compliance**: Candidate A failed the mandatory `documentation_synchronized` pass bar by letting documentation drift completely. In contrast, Candidate B updated `README.md` with comprehensive contract specifications.
2. **Superior Refactoring Craft**: Candidate B adhered to fundamental DRY principles by extracting `_is_valid_tenant`, creating a single source of truth for tenant validation across both `append()` and `migrate()`. Candidate A introduced duplicated validation rules and confusing inverted logic (`_needs_migration`).
3. **Engineering Rigor**: Candidate B demonstrated holism—pairing clean, idiomatic code with contract documentation synchronization, ensuring the repository remains maintainable and true to production engineering standards.
