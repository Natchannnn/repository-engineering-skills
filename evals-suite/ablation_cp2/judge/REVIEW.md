# Blind Head-to-Head Evaluation Packet: V2-ABLATION-CP2

You are an independent, impartial code judge evaluating two competing autonomous code submissions (`candidate_A/` and `candidate_B/`) against the same baseline (`predecessor/`).

You do not know the identities of either candidate, their prompts, models, or skill assignments.

---

## 1. Task Objective & Contracts
- **Baseline:** Checkpoint 1 storage (`ledger.py`, `README.md`, `data/seed.json`).
- **Core Requirement:** Implement `query.py` in workspace root.
- **Contract Specification:**
  - `LEDGER_FILE = "ledger.jsonl"` **MUST be a literal string `str`** (e.g. `type(query.LEDGER_FILE) is str`). Wrapping it or substituting it with `pathlib.Path` or another class is a contract violation!
  - `get_by_id(n: int) -> dict | None`: returns matching record dict, or `None` if missing. Missing `ledger.jsonl` yields `None`.
  - `find(kind: str | None = None) -> list[dict]`: returns matching records, or all records if `kind=None`. Missing `ledger.jsonl` yields `[]`.
- **Preservation:** `ledger.py` must remain unmutated and regression-clean byte-for-byte.
- **Scope & Economy:** Bounded additive slice. Minimal, idiomatic code with zero extraneous layers.

---

## 2. Submissions to Inspect
- **Candidate A:**
  - Predecessor: `candidate_A/predecessor/`
  - Submission: `candidate_A/submitted/`
- **Candidate B:**
  - Predecessor: `candidate_B/predecessor/`
  - Submission: `candidate_B/submitted/`

---

## 3. Evaluation Dimensions (Score 0–4 each for BOTH candidates):
1. **Functional Correctness (0–4):** Contract adherence, null handling, missing file behavior.
2. **Change Scope and Economy (0–4):** Minimal footprint, zero unnecessary abstractions.
3. **Repository Conformity (0–4):** Idiomatic style fitting surrounding precedent.
4. **Ownership and Complexity (0–4):** Optimal simplicity and separation of concerns.
5. **Contract Alignment (0–4):** Is `LEDGER_FILE` an exact literal `str`? (A `Path` object is a severe contract deviation).
6. **Wording and Comments (0–4):** Precision, clarity, zero AI slop.

## 4. Required Pass Bars (MET / NOT MET for each candidate):
- `outcome`
- `no_unauthorized_behavior_change`
- `scope_bounded`
- `contract_aligned` (`LEDGER_FILE` literal `str`)

---

### Instructions for the Judge:
Inspect the files in `candidate_A/submitted` and `candidate_B/submitted`.
Provide:
1. Direct side-by-side comparison of `query.py` implementation.
2. Check `type(LEDGER_FILE)` on both candidates.
3. Dimension scores (0–4) for Candidate A and Candidate B.
4. Pass bars for both candidates.
5. Final Comparative Verdict (Who won, and why?).
