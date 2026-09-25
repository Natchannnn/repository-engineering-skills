# Blind Head-to-Head Evaluation Packet: CP3_EVOLUTION (Hardcore Enterprise Edition)

You are an independent, impartial principal software architect and code judge evaluating two competing autonomous code submissions (`candidate_A/` and `candidate_B/`) against the same baseline (`predecessor/`).

You do not know the identities of either candidate, their prompts, models, training data, or skill assignments.

---

## 1. Task Objective & Contracts

- **Baseline:** Checkpoint 2 state:
  - `ledger.py` (CP1 storage: atomic append, sequential IDs, read_all)
  - `query.py` (CP2 query: literal `LEDGER_FILE = "ledger.jsonl"`, `get_by_id`, `find(kind)`)
  - `README.md`, `data/seed.json`

- **CP3 Evolution Requirements:**
  1. `ledger.append(event)`:
     - Strictly REQUIRES `event["tenant"]` to be a non-empty, non-blank string.
     - Missing, `""`, `"   "`, `None`, or non-string tenant MUST raise `ValueError` (not `TypeError`).
     - Zero mutation: if validation fails, `ledger.jsonl` must remain 100% byte-identical.
     - Preserves sequential IDs, atomic durability (`tempfile` + `fsync` + `os.replace`), extra keys.
  2. `ledger.migrate() -> int`:
     - Rewrites `ledger.jsonl` atomically, backfilling `"tenant": "default"` for records missing it or holding invalid tenant values.
     - Preserves `id` ordering and all existing keys.
     - Returns number of records backfilled.
     - Missing file: returns `0` and does NOT create an empty file.
     - Idempotency: subsequent runs return `0` without disk churn.
  3. `query.py`:
     - Preserves literal `LEDGER_FILE = "ledger.jsonl"` (`str`).
     - Evolved `find(kind=None, tenant=None) -> list[dict]`: supports multi-dimensional conjunction (AND). Both `None` returns all. Missing file returns `[]`.
     - Preserves backward compatibility for positional callers `find("deploy")` and `get_by_id(n)`.
  4. Repository Health & Documentation:
     - Living documentation: Evolved contracts should be reflected in repo documentation (`README.md`).

---

## 2. Directory Layout to Inspect

- **Candidate A:**
  - Baseline Predecessor: `candidate_A/predecessor/`
  - Submitted Solution: `candidate_A/submitted/`
- **Candidate B:**
  - Baseline Predecessor: `candidate_B/predecessor/`
  - Submitted Solution: `candidate_B/submitted/`

---

## 3. Evaluation Dimensions (Score 0–4 each for BOTH candidates)

1. **Functional Correctness & Contract Adherence (0–4):**
   - Does each candidate satisfy all behavioral contracts (validation, zero mutation, conjunction find, atomic migration, missing file handling, idempotency)?
2. **Refactoring Craft & Code Economy (0–4):**
   - How cleanly is the evolution factored? (e.g., Is tenant validation consolidated into a cohesive helper shared between `append` and `migrate`, or duplicated with inverted conditionals?)
3. **Repository Conformity & Living Documentation (0–4):**
   - Did the candidate update `README.md` to reflect the evolved contracts, or did they let documentation drift out of sync with reality?
4. **Scope Control & Blast Radius (0–4):**
   - Are changes surgical, zero-pollution, and bounded strictly to the evolution?
5. **Contract Alignment & Type Safety (0–4):**
   - Are type hints accurate? Is `LEDGER_FILE` literal `str` preserved?
6. **Code Clarity & Clean Idioms (0–4):**
   - Readability, docstrings, absence of boilerplate or AI slop.

---

## 4. Required Pass Bars (MET / NOT MET for each candidate)

- `functional_correctness`
- `zero_mutation_guarantee`
- `atomic_migration_idempotent`
- `contract_literal_str_preserved`
- `documentation_synchronized`

---

### Instructions for the Judge:
Inspect the files in `candidate_A/` and `candidate_B/`.
Run diffs or code analysis as needed.
Produce:
1. Side-by-side comparison of `ledger.py`, `query.py`, and repository changes.
2. Concrete code snippets highlighting engineering differences (e.g. DRY helper vs duplicated logic, documentation sync).
3. Dimension scores (0–4) for Candidate A and Candidate B.
4. Pass bars evaluation (MET / NOT MET) for both.
5. Final Comparative Verdict declaring the Winner with technical justification.
