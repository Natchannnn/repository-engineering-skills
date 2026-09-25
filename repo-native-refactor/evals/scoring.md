# Evaluation Scoring

Evaluate the produced diff and completion report, not whether the response repeats skill headings or preferred wording.

Use `harness.py` and [the harness protocol](HARNESS.md) for executable repository evaluations. This rubric is frozen before dispatch and included in judge packets. Never copy it or the fixtures into a runner packet.

## Hard failures

Any of the following fails the evaluation regardless of other improvements:

- unauthorized observable behavior change;
- removal of intentionally used code;
- weakened or deleted valid regression coverage;
- edits to generated, vendored, or history-sensitive artifacts outside their workflow;
- unjustified high-risk bulk rewrite;
- fabricated ticket, incident, owner, compatibility claim, or production history;
- reworded error, log, event, stdout, stderr, snapshot, or user-facing copy without contract analysis;
- unrelated modernization that materially expands scope.

## Quality dimensions

Score each applicable dimension from 0 to 4:

### Semantic integrity

- **4:** behavior and relevant contracts are preserved or an authorized correction is explicit and verified;
- **3:** no known regression, with a clearly stated verification limitation;
- **2:** preservation is plausible but important evidence was not inspected;
- **1:** semantic drift is likely;
- **0:** known unauthorized regression.

### Repository conformity

- **4:** decisions follow relevant ownership, domain language, architecture, and local conventions with evidence;
- **3:** mostly native with minor unsupported choices;
- **2:** generic good practice dominates local evidence;
- **1:** a foreign style or parallel system is introduced;
- **0:** repository contracts or architecture are contradicted.

### Prose integrity

- **4:** redundant prose is deleted, valuable rationale is preserved or tightened, terminology is native, and observable wording is protected;
- **3:** correct decisions with minor voice mismatch or residue;
- **2:** long comments are merely paraphrased or useful prose remains generic;
- **1:** meaningful rationale is removed or empty narration is added;
- **0:** contractual prose changes or invented rationale cause harm.

### Maintainability and ownership

- **4:** the smallest adequate correction reduces accidental complexity in the correct owner;
- **3:** clear improvement with minor avoidable churn;
- **2:** mixed improvement and new indirection;
- **1:** broad cleanup obscures ownership;
- **0:** architecture or dependency direction regresses.

### Reviewability and scope

- **4:** every changed line is defensible, bounded, and supported by verification;
- **3:** coherent with small unrelated noise;
- **2:** difficult to review or mixes concerns;
- **1:** broad speculative rewrite;
- **0:** user changes are overwritten or scope is materially violated.

## Rating conversion

Only passing judgments with no failed or invalid machine gate receive a quality rating. Required bar failures cannot coexist with an overall pass. Displayed averages may round; full-mark flags require every dimension score to be 4.

- **9.0 or higher:** at least 90% of applicable points;
- **9.5 or higher:** at least 95% of applicable points;
- **10.0:** all applicable points on the current benchmark, not universal perfection.

Compare skill and baseline runs on the same fixture and model settings. Record instruction tokens loaded, references selected, changed-line count, verification performed, and residual uncertainty. Token savings never compensate for a hard failure.

Do not certify from a single run, a failed or skipped baseline, an unjudged artifact, or a judge that saw variant identity or an expected patch. Report pass rate, minimum score, and dispersion across repeated runs. A `10.0` means full marks on the frozen benchmark only.
