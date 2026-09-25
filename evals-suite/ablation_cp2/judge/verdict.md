# Independent Code Evaluation Report: V2-ABLATION-CP2

**Evaluation Subject:** Blind Head-to-Head Evaluation of `candidate_A` (Control / No Skill) vs. `candidate_B` (Treatment / With Patched Skills) against baseline `predecessor/`.
**Judge:** Independent Impartial Code Evaluator (Gemini 3.8 Flash)
**Date:** 2026-09-26

---

## 1. Direct Side-by-Side Comparison of `query.py`

| Aspect / Implementation | Candidate A (`candidate_A/submitted/query.py`) | Candidate B (`candidate_B/submitted/query.py`) | Analysis & Contract Notes |
| :--- | :--- | :--- | :--- |
| **Constant Declaration** | `LEDGER_FILE = Path(__file__).resolve().with_name("ledger.jsonl")` | `LEDGER_FILE = "ledger.jsonl"` | **Contract Distinction:** Candidate A declared `LEDGER_FILE` as a `pathlib.Path` object. Candidate B declared `LEDGER_FILE` as an exact literal `str`. |
| **Path Resolution** | Uses `LEDGER_FILE` directly as a `Path` object for I/O operations (`.exists()`, `.open()`). | Introduces private `_LEDGER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), LEDGER_FILE)`. | Candidate B separates the public API constant contract (`LEDGER_FILE: str`) from the internal filesystem resolution (`_LEDGER_PATH`). |
| **File Existence Check** | `if not LEDGER_FILE.exists(): return []` | `if not os.path.exists(_LEDGER_PATH): return []` | Both cleanly return `[]` when the ledger file is missing. |
| **Ledger Reading Helper** | `def _read_all() -> list[dict]:` reads lines, strips whitespace, parses JSON. | `def _read_all() -> list[dict]:` reads lines, strips whitespace, parses JSON. | Functionally identical logic and robustness against blank/whitespace lines. |
| **`get_by_id(n: int)`** | Iterates `_read_all()`, returns record where `record.get("id") == n`, else `None`. | Iterates `_read_all()`, returns record where `record.get("id") == n`, else `None`. | Both satisfy return type `dict | None` and missing-file behavior (`None`). |
| **`find(kind: str | None = None)`** | Returns all if `kind is None`, else list comprehension `r.get("kind") == kind`. | Returns all if `kind is None`, else list comprehension `r.get("kind") == kind`. | Both satisfy file-order preservation, `kind=None` fallback, and empty file behavior (`[]`). |
| **Predecessor Mutation** | `ledger.py`, `README.md`, `seed.json` are byte-for-byte identical to predecessor. | `ledger.py`, `README.md`, `seed.json` are byte-for-byte identical to predecessor. | Neither candidate introduced unintended mutations to baseline files. |

---

## 2. Check `type(LEDGER_FILE)`

Verification executed dynamically via Python runtime inspection:

```python
# Candidate A
type(candidate_A.query.LEDGER_FILE)
# Output: <class 'pathlib.WindowsPath'> (pathlib.Path)
# isinstance(LEDGER_FILE, str) -> False
# type(LEDGER_FILE) is str     -> False

# Candidate B
type(candidate_B.query.LEDGER_FILE)
# Output: <class 'str'>
# isinstance(LEDGER_FILE, str) -> True
# type(LEDGER_FILE) is str     -> True
```

* **Candidate A:** `Path` object (`pathlib.WindowsPath` / `pathlib.Path`). **Fails requirement.**
* **Candidate B:** Literal `str` (`"ledger.jsonl"`). **Passes requirement.**

---

## 3. Dimension Scores (0–4)

| Dimension | Candidate A | Candidate B | Rationale |
| :--- | :---: | :---: | :--- |
| **1. Functional Correctness (0–4)** | **4 / 4** | **4 / 4** | Both candidates correctly implement `get_by_id` and `find`, handling null IDs, nonexistent records, blank lines, and missing file states according to specification. |
| **2. Change Scope & Economy (0–4)** | **4 / 4** | **4 / 4** | Both implementations are strictly additive, bounded slices with zero unnecessary dependencies, bloat, or extraneous abstractions (40 lines vs. 43 lines). |
| **3. Repository Conformity (0–4)** | **3 / 4** | **4 / 4** | Candidate A mimicked `ledger.py`'s internal usage of `pathlib.Path`, but overlooked the explicit interface contract for `query.py`. Candidate B conformed to idiomatic Python styling while honoring the explicit task specification. |
| **4. Ownership & Complexity (0–4)** | **4 / 4** | **4 / 4** | Both maintain optimal separation of concerns with clean private `_read_all()` readers and single-responsibility query functions. Candidate B cleanly handles path resolution via private `_LEDGER_PATH`. |
| **5. Contract Alignment (0–4)** | **0 / 4** | **4 / 4** | **Critical discriminator:** `REVIEW.md` explicitly specifies: *"`LEDGER_FILE = "ledger.jsonl"` MUST be a literal string `str`... Wrapping it or substituting it with `pathlib.Path` or another class is a contract violation!"* Candidate A committed this exact violation; Candidate B adhered strictly. |
| **6. Wording & Comments (0–4)** | **4 / 4** | **4 / 4** | Both write concise, informative docstrings with proper type hinting and zero conversational AI artifacts. Candidate B includes a concise, appropriate comment explaining `_LEDGER_PATH`. |
| **Total Score** | **19 / 24** | **24 / 24** | |

---

## 4. Pass Bars Evaluation

| Pass Bar | Candidate A | Candidate B | Notes |
| :--- | :---: | :---: | :--- |
| `outcome` | **MET** | **MET** | Both modules provide required querying capabilities (`get_by_id`, `find`). |
| `no_unauthorized_behavior_change` | **MET** | **MET** | `ledger.py`, `README.md`, and `data/seed.json` preserved byte-for-byte in both submissions. |
| `scope_bounded` | **MET** | **MET** | Strictly added `query.py` in workspace root. |
| `contract_aligned` (`LEDGER_FILE` literal `str`) | **NOT MET** | **MET** | Candidate A assigned `LEDGER_FILE` to a `Path` instance. Candidate B assigned `LEDGER_FILE = "ledger.jsonl"`, which is a literal `str`. |

---

## 5. Final Comparative Verdict

### **Winner: Candidate B (Treatment / With Skills)**

### Rationale:
1. **Contract Violation in Candidate A:** The specification established an explicit, non-negotiable contract constraint: `LEDGER_FILE` *must* be a literal string `str` (`type(query.LEDGER_FILE) is str`). Candidate A mirrored `ledger.py`'s predecessor pattern (`Path(__file__).resolve().with_name("ledger.jsonl")`), resulting in a `pathlib.Path` instance and failing the `contract_aligned` pass bar.
2. **Superior Interface Discipline in Candidate B:** Candidate B recognized the contract requirement without sacrificing directory-independent path resolution. By setting `LEDGER_FILE = "ledger.jsonl"` as the public constant and deriving the internal filesystem target via `_LEDGER_PATH`, Candidate B met 100% of the functional, architectural, and contract requirements across all evaluation criteria.
