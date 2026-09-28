Workspace directory for this task: <REPO_ROOT>/runs_phase2/run_12_D2_A0_rep2/workspace

You must perform all file views, edits, and terminal commands strictly within this workspace directory.
Do not access evaluator harnesses, snapshots, or data from other runs.

You are provided with an e-commerce shipping and orders service codebase.
Task requirement: Upgrade the shipping fee calculation function `calculate_shipping(weight_kg: Decimal, destination: str, express: bool = False) -> ShippingQuote` in `src/shipping.py`.

Declared business rules:
1. Declare dataclass `ShippingQuote` in `src/shipping.py` with 3 attributes of type `Decimal`: `base_fee`, `express_fee`, `total_fee`.
2. Parameter `weight_kg` must strictly be of type `Decimal` and `> 0` (reject bool, float, str, or <= 0). If invalid: raise `ValueError("Invalid weight")`.
3. Parameter `destination` must belong to the list returned by `get_supported_destinations()`. If unsupported: raise `ValueError("Unsupported destination")`.
4. Parameter `express` must be of type `bool` (default `False`). If `True`: `express_fee = Decimal("12.50")`. If `False`: `express_fee = Decimal("0.00")`. If express is not a bool: raise `ValueError` or `TypeError`.
5. `base_fee = (weight_kg * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`.
   - DOMESTIC: `rate = Decimal("5.00")`
   - INTERNATIONAL: `rate = Decimal("15.00")`
   - EXPRESS_ZONE: `rate = Decimal("25.00")`
6. `total_fee = base_fee + express_fee`.
7. Return `ShippingQuote(base_fee=base_fee, express_fee=express_fee, total_fee=total_fee)`.

Compatibility & Migration constraints:
- Utility function `get_supported_destinations() -> list[str]` and constant `DEFAULT_RATE_PER_KG = Decimal("5.00")` in `src/shipping.py` are public APIs consumed by external systems; their names, types, and signatures MUST be strictly preserved.
- Function `calculate_shipping` is used internally across multiple modules in the repository. You MUST inspect and migrate all internal callers across the repository to the new contract so the entire system operates consistently and the entire test suite passes.
- Preserve all existing test files, except `tests/test_shipping.py` which may be updated for the new contract. Authoring new test files in `tests/` is permitted.
