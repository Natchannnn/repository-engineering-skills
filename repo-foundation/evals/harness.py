"""Multi-Checkpoint Foundation Evaluation Harness (repo-foundation).

Provides deterministic verification, byte-level snapshots, and scoring
for repository lifecycle milestones:
- CP1_BOOTSTRAP: Initial baseline, append-only persistence, atomic fsync.
- CP2_SLICE: Greenfield additive query slice, strict type contract adherence.
- CP3_EVOLUTION: Contract evolution, multi-tenant validation, atomic migration.
- CP4_CONTINUITY: Multi-session continuity, regression resilience.
"""

from __future__ import annotations

import argparse
import json
import os
import py_compile
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
from fractions import Fraction
from pathlib import Path

# Local imports
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    import byte_snapshot
    import core
except ImportError:
    from . import byte_snapshot
    from . import core


CHECKPOINT_CHECKS: dict[str, list[str]] = {
    "CP1_BOOTSTRAP": ["check_cp1_accept.py"],
    "CP2_SLICE": ["check_cp2_accept.py", "check_store_regress.py"],
    "CP3_EVOLUTION": ["check_cp3_accept.py", "check_query_regress.py", "check_tenant_regress.py"],
    "CP4_CONTINUITY": ["check_cp4_accept.py", "check_store_regress.py", "check_query_regress.py", "check_tenant_regress.py"],
}


EXPECTED_SCHEMAS = [
    "checkpoint-record-v1.json",
    "journey-v1.json",
    "judge-index-v1.json",
    "judge-packet-v1.json",
    "judgment-v1.json",
    "manifest-v1.json",
    "pre-check-artifact-v1.json",
    "rubric-v1.json",
    "score-report-v1.json",
    "scoring-policy-v1.json",
]


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate internal schemas, rubric, policy, tasks, and compile verification scripts."""
    print("Validating repo-foundation evaluation assets...")

    # 1. Schemas directory
    schemas_dir = SCRIPT_DIR / "schemas"
    if not schemas_dir.is_dir():
        print(f"FAIL: Schemas directory missing: {schemas_dir}")
        return 1

    schema_count = 0
    for s_name in EXPECTED_SCHEMAS:
        s_file = schemas_dir / s_name
        if not s_file.exists():
            print(f"FAIL: Required schema file missing: {s_name}")
            return 1
        try:
            s_data = json.loads(s_file.read_text(encoding="utf-8"))
            core.validate_json_schema_definition(s_data, s_name)
            schema_count += 1
        except Exception as e:
            print(f"FAIL: Schema invalid: {s_name}: {e}")
            return 1
    print(f"[OK] All {schema_count}/10 required JSON schemas present and verified structurally against specification")
    
    # 2. Rubric
    rubric_path = SCRIPT_DIR / "rubric.json"
    if not rubric_path.exists():
        print(f"FAIL: {rubric_path} missing")
        return 1
    try:
        rubric = json.loads(rubric_path.read_text(encoding="utf-8"))
        core.validate_rubric_schema(rubric)
        dim_list = rubric.get("dimensions", [])
        print(f"[OK] Rubric valid ({len(dim_list)} dimensions)")
    except Exception as e:
        print(f"FAIL: Rubric invalid: {e}")
        return 1

    # 3. Scoring Policy
    policy_path = SCRIPT_DIR / "scoring_policy.json"
    if not policy_path.exists():
        print(f"FAIL: {policy_path} missing")
        return 1
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        core.validate_scoring_policy_schema(policy)
        print("[OK] Scoring policy valid")
    except Exception as e:
        print(f"FAIL: Scoring policy invalid: {e}")
        return 1

    # 4. Tasks
    tasks_dir = SCRIPT_DIR / "tasks"
    for cp_id in core.CHECKPOINT_IDS:
        task_file = tasks_dir / f"{cp_id}.md"
        if not task_file.exists():
            print(f"FAIL: Task spec missing: {task_file}")
            return 1
        content = task_file.read_text(encoding="utf-8").strip()
        if not content.startswith("# CP"):
            print(f"FAIL: Task spec header malformed: {task_file.name}")
            return 1
    print(f"[OK] All {len(core.CHECKPOINT_IDS)} milestone task specs present and verified")

    # 5. Trusted Checks (Syntax compilation and bindings)
    checks_dir = SCRIPT_DIR / "trusted_checks"
    distinct_scripts = sorted({chk for checks in CHECKPOINT_CHECKS.values() for chk in checks})
    for chk_name in distinct_scripts:
        p = checks_dir / chk_name
        if not p.exists():
            print(f"FAIL: Trusted check missing: {p}")
            return 1
        try:
            py_compile.compile(str(p), doraise=True)
        except Exception as e:
            print(f"FAIL: Trusted check syntax error in {chk_name}: {e}")
            return 1

    total_bindings = sum(len(checks) for checks in CHECKPOINT_CHECKS.values())
    print(f"[OK] All {len(distinct_scripts)} distinct trusted verification scripts compiled successfully ({total_bindings} checkpoint bindings verified)")
    print("\nALL EVALUATION ASSETS VALIDATED SUCCESSFULLY.")
    return 0


def deploy_snapshot_bundle(staging_bundle: Path, final_dest: Path, expected_hash: str) -> None:
    """Safely deploy or update a snapshot bundle at final_dest with rollback on failure.

    Invariants:
    1. Pre-mutation destination validation: if final_dest exists, it MUST be a valid bundle.
       If it is invalid or contains unmanaged files, reject immediately with HarnessError
       without mutating the destination filesystem.
    2. Idempotent reuse: if final_dest is already a valid bundle with identical expected_hash,
       reuse it cleanly without rewriting.
    3. If replacing an existing valid bundle with a different hash, stage replacement on the target
       filesystem first, preserve previous bundle in a backup, atomic swap, and rollback if failure occurs.
    """
    final_dest = final_dest.resolve()

    # 1. Inspect existing destination before any mutation
    if final_dest.exists():
        is_valid, reason = core.is_valid_snapshot_bundle(final_dest)
        if not is_valid:
            raise core.HarnessError(f"Destination directory cannot be overwritten: {reason}")

        # 2. Idempotent reuse: if destination is already an identical valid bundle, preserve it
        if final_dest.is_dir():
            existing_files = final_dest / "files"
            if existing_files.is_dir() and core.tree_hash(existing_files).lower() == expected_hash.lower():
                return

    final_dest.parent.mkdir(parents=True, exist_ok=True)

    # 3. Stage new bundle on destination filesystem
    token = secrets.token_hex(4)
    tmp_deploy = final_dest.parent / f".deploy_{final_dest.name}_{token}"
    backup_dir: Path | None = None

    try:
        shutil.copytree(staging_bundle, tmp_deploy)
        core.verify_bundle_dir(tmp_deploy, expected_hash=expected_hash)

        # 4. If destination exists, move it to backup on same filesystem
        if final_dest.exists():
            backup_dir = final_dest.parent / f".backup_{final_dest.name}_{token}"
            final_dest.rename(backup_dir)

        # 5. Atomic move staged bundle into destination
        try:
            tmp_deploy.rename(final_dest)
        except Exception:
            if backup_dir and backup_dir.exists() and not final_dest.exists():
                backup_dir.rename(final_dest)
            raise

        # 6. Verify final destination on disk
        core.verify_bundle_dir(final_dest, expected_hash=expected_hash)

        # Success: safely prune backup
        if backup_dir and backup_dir.exists():
            shutil.rmtree(backup_dir, ignore_errors=True)

    except Exception:
        # Failure recovery: clean up incomplete deployment and restore backup
        if tmp_deploy.exists():
            shutil.rmtree(tmp_deploy, ignore_errors=True)
        if final_dest.exists() and backup_dir and backup_dir.exists():
            shutil.rmtree(final_dest, ignore_errors=True)
        if backup_dir and backup_dir.exists() and not final_dest.exists():
            backup_dir.rename(final_dest)
        raise


def cmd_snapshot(args: argparse.Namespace) -> int:
    """Take a deterministic byte-exact snapshot of a workspace."""
    target_dir = Path(args.dir).resolve()
    if not target_dir.is_dir():
        print(f"FAIL: Target directory does not exist: {target_dir}")
        return 1

    final_out: Path | None = Path(args.out).resolve() if args.out else None

    # Pre-mutation safety checks on output destination
    if final_out is not None:
        if core.paths_overlap(target_dir, final_out):
            print(f"FAIL: Snapshot output path overlaps with or contains target directory: {final_out}")
            return 1

        is_json_manifest = str(final_out).endswith(".json")
        if is_json_manifest:
            if final_out.is_dir():
                print(f"FAIL: Manifest destination is an existing directory: {final_out}")
                return 1
        else:
            is_valid, reason = core.is_valid_snapshot_bundle(final_out)
            if not is_valid:
                print(f"FAIL: Destination directory cannot be overwritten: {reason}")
                return 1

    # Stage snapshot in an isolated temporary directory
    stage_root = Path(tempfile.mkdtemp(prefix="rf_snap_stage_"))
    try:
        tree_hash, snap_dir = byte_snapshot.create_snapshot(target_dir, stage_root)
        meta_json = snap_dir / "snapshot.json"

        # Verify staging integrity before touching any final destination
        byte_snapshot.verify_snapshot_integrity(tree_hash, stage_root)

        if final_out is not None:
            if str(final_out).endswith(".json"):
                final_out.parent.mkdir(parents=True, exist_ok=True)
                tmp_json = final_out.parent / f".tmp_{final_out.name}_{secrets.token_hex(4)}"
                shutil.copy2(meta_json, tmp_json)
                os.replace(tmp_json, final_out)
                print(f"Snapshot successfully created for: {target_dir}")
                print(f"Tree Hash (SHA-256): {tree_hash}")
                print(f"Snapshot Manifest:  {final_out}")
                print(f"Preserved manifest JSON to: {final_out}")
            else:
                try:
                    deploy_snapshot_bundle(snap_dir, final_out, tree_hash)
                except Exception as e:
                    print(f"FAIL: {e}")
                    return 1

                print(f"Snapshot successfully created for: {target_dir}")
                print(f"Tree Hash (SHA-256): {tree_hash}")
                print(f"Snapshot Directory: {final_out}")
                print(f"Snapshot Manifest:  {final_out / 'snapshot.json'}")
                print(f"Preserved and verified full snapshot bundle to: {final_out}")
        else:
            default_persistent_dir = SCRIPT_DIR / "control" / "snapshots" / tree_hash
            try:
                deploy_snapshot_bundle(snap_dir, default_persistent_dir, tree_hash)
            except Exception as e:
                print(f"FAIL: {e}")
                return 1

            print(f"Snapshot successfully created for: {target_dir}")
            print(f"Tree Hash (SHA-256): {tree_hash}")
            print(f"Snapshot Directory: {default_persistent_dir}")
            print(f"Snapshot Manifest:  {default_persistent_dir / 'snapshot.json'}")
    finally:
        shutil.rmtree(stage_root, ignore_errors=True)

    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    """Execute trusted acceptance & regression checks against a workspace."""
    cp_id = args.checkpoint.upper()
    if cp_id not in CHECKPOINT_CHECKS:
        print(f"FAIL: Unknown checkpoint: {cp_id}. Valid: {list(CHECKPOINT_CHECKS.keys())}")
        return 1

    ws_path = Path(args.workspace).resolve()
    if not ws_path.is_dir():
        print(f"FAIL: Workspace does not exist: {ws_path}")
        return 1

    checks_to_run = CHECKPOINT_CHECKS[cp_id]
    checks_dir = SCRIPT_DIR / "trusted_checks"

    print(f"\n=======================================================")
    print(f"VERIFYING {cp_id} ON: {ws_path}")
    print(f"Checks to execute: {', '.join(checks_to_run)}")
    print(f"=======================================================")

    all_passed = True
    for chk_name in checks_to_run:
        chk_script = checks_dir / chk_name
        if not chk_script.exists():
            print(f"[FAIL] Missing check script: {chk_script}")
            all_passed = False
            continue

        tmp_run = Path(tempfile.mkdtemp(prefix=f"eval_{cp_id}_"))
        try:
            tmp_ws = tmp_run / "workspace"
            shutil.copytree(ws_path, tmp_ws)

            tmp_chk = tmp_run / chk_name
            shutil.copy2(chk_script, tmp_chk)

            # Adapt Linux /workspace or /tmp paths if running on Windows/custom sandbox
            chk_code = chk_script.read_text(encoding="utf-8")
            tmp_target = (tmp_run / "tmp_target").resolve()
            ws_str = repr(str(tmp_ws.resolve()))
            target_str = repr(str(tmp_target))
            chk_code = re.sub(r'WS\s*=\s*Path\([^)]+\)', lambda _: f"WS = Path({ws_str})", chk_code)
            chk_code = re.sub(r'TMP\s*=\s*Path\([^)]+\)', lambda _: f"TMP = Path({target_str})", chk_code)
            
            run_script = tmp_run / f"run_{chk_name}"
            run_script.write_text(chk_code, encoding="utf-8")

            proc = subprocess.run(
                [sys.executable, str(run_script)],
                cwd=str(tmp_ws),
                capture_output=True,
                text=True,
                timeout=args.timeout or 30,
            )

            if proc.returncode == 0:
                print(f"[PASS] {chk_name}: {proc.stdout.strip()}")
            else:
                all_passed = False
                print(f"[FAIL] {chk_name} (exit code {proc.returncode})")
                if proc.stdout.strip():
                    print(f"  stdout: {proc.stdout.strip()}")
                if proc.stderr.strip():
                    print(f"  stderr: {proc.stderr.strip()}")

        except subprocess.TimeoutExpired:
            all_passed = False
            print(f"[TIMEOUT] {chk_name} exceeded {args.timeout or 30}s")
        except Exception as e:
            all_passed = False
            print(f"[ERROR] {chk_name} exception: {e}")
        finally:
            shutil.rmtree(tmp_run, ignore_errors=True)

    print(f"\nRESULT FOR {cp_id}: {'ALL CHECKS PASSED' if all_passed else 'VERIFICATION FAILED'}")
    return 0 if all_passed else 1


def cmd_score(args: argparse.Namespace) -> int:
    """Compute score report from judgment and rubric matching canonical judgment-v1 schema."""
    judgment_path = Path(args.judgment).resolve()
    if not judgment_path.exists():
        print(f"FAIL: Judgment file missing: {judgment_path}")
        return 1

    rubric_path = Path(args.rubric or SCRIPT_DIR / "rubric.json").resolve()
    policy_path = Path(args.policy or SCRIPT_DIR / "scoring_policy.json").resolve()

    try:
        judgment = json.loads(judgment_path.read_text(encoding="utf-8"))
        core.validate_judgment_schema(judgment)
    except Exception as e:
        print(f"FAIL: Judgment invalid per schema: {e}")
        return 1

    try:
        rubric = json.loads(rubric_path.read_text(encoding="utf-8"))
        core.validate_rubric_schema(rubric)
    except Exception as e:
        print(f"FAIL: Rubric invalid per schema: {e}")
        return 1

    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        core.validate_scoring_policy_schema(policy)
    except Exception as e:
        print(f"FAIL: Scoring policy invalid per schema: {e}")
        return 1

    # Map all defined rubric dimensions and required bars
    rubric_dims = {d["id"]: d for d in rubric.get("dimensions", [])}
    rubric_bars = {b["id"]: b for b in rubric.get("required_bars", [])}

    # Determine target checkpoint if specified, or infer from dimensions/bars
    cp_id = getattr(args, "checkpoint", None)
    if cp_id:
        cp_id = cp_id.upper()
        if cp_id not in core.CHECKPOINT_IDS:
            print(f"FAIL: Unknown checkpoint: {cp_id}. Valid: {core.CHECKPOINT_IDS}")
            return 1
    else:
        judged_dim_ids = {d.get("id") for d in judgment.get("dimensions", []) if isinstance(d, dict)}
        judged_bar_ids = {b.get("id") for b in judgment.get("bar_evidence", []) if isinstance(b, dict)}
        if "takeover_readiness" in judged_dim_ids or "takeover_effective" in judged_bar_ids:
            cp_id = "CP4_CONTINUITY"
        elif "contract_evolution" in judged_dim_ids or "evolution_coherent" in judged_bar_ids:
            cp_id = "CP3_EVOLUTION"
        else:
            cp_id = "CP2_SLICE"

    # Determine expected dimensions and bars for this checkpoint
    expected_dim_ids = {
        d_id for d_id, d_meta in rubric_dims.items()
        if cp_id in d_meta.get("applicable_checkpoints", [])
    }
    expected_bar_ids = {
        b_id for b_id, b_meta in rubric_bars.items()
        if cp_id in b_meta.get("applicable_checkpoints", [])
    }

    # Extract dimensions from canonical judgment-v1
    judged_dims = judgment.get("dimensions", [])
    seen_dims = set()
    scores_by_dim: dict[str, float] = {}
    validation_errors = []

    for d_entry in judged_dims:
        if not isinstance(d_entry, dict):
            validation_errors.append("Dimension entry must be an object")
            continue
        d_id = d_entry.get("id")
        score = d_entry.get("score")

        if d_id not in rubric_dims:
            validation_errors.append(f"Unknown dimension ID: '{d_id}'")
            continue

        if d_id not in expected_dim_ids:
            validation_errors.append(f"Dimension '{d_id}' is not applicable to checkpoint '{cp_id}'")
            continue

        if d_id in seen_dims:
            validation_errors.append(f"Duplicate dimension ID: '{d_id}'")
            continue
        seen_dims.add(d_id)

        if score is None:
            validation_errors.append(f"Dimension '{d_id}' has null score")
            continue

        if not isinstance(score, int) or score < 0 or score > 4:
            validation_errors.append(f"Dimension '{d_id}' score must be integer between 0 and 4, got {score}")
            continue

        scores_by_dim[d_id] = int(score)

    missing_dims = expected_dim_ids - seen_dims
    if missing_dims:
        validation_errors.append(f"Missing required dimensions for {cp_id}: {sorted(missing_dims)}")

    # Extract bar evidence from canonical judgment-v1
    judged_bars = judgment.get("bar_evidence", [])
    seen_bars = set()
    bar_verdicts: dict[str, str] = {}

    for b_entry in judged_bars:
        if not isinstance(b_entry, dict):
            validation_errors.append("Bar entry must be an object")
            continue
        b_id = b_entry.get("id")
        b_verdict = b_entry.get("verdict")

        if b_id not in rubric_bars:
            validation_errors.append(f"Unknown bar ID: '{b_id}'")
            continue

        if b_id not in expected_bar_ids:
            validation_errors.append(f"Bar '{b_id}' is not applicable to checkpoint '{cp_id}'")
            continue

        if b_id in seen_bars:
            validation_errors.append(f"Duplicate bar ID: '{b_id}'")
            continue
        seen_bars.add(b_id)

        bar_verdicts[b_id] = b_verdict

    missing_bars = expected_bar_ids - seen_bars
    if missing_bars:
        validation_errors.append(f"Missing required bars for {cp_id}: {sorted(missing_bars)}")

    hard_failures = judgment.get("hard_failures", [])
    if hard_failures:
        validation_errors.append(f"Hard failures reported: {hard_failures}")

    overall_verdict = judgment.get("verdict")
    if overall_verdict != "pass":
        validation_errors.append(f"Overall judgment verdict is '{overall_verdict}' (expected 'pass')")

    if validation_errors:
        print("========================================")
        print("FOUNDATION EVALUATION REJECTED")
        print("========================================")
        print(f"Checkpoint evaluated: {cp_id}")
        for err in validation_errors:
            print(f"  [ERROR] {err}")
        print("----------------------------------------")
        print("Final Certification: FAILED (incomplete or invalid evidence)")
        return 1

    total_weighted_frac = Fraction(0, 1)
    total_weight_frac = Fraction(0, 1)
    for dim_id, score in scores_by_dim.items():
        raw_w = rubric_dims[dim_id].get("weight", 1)
        if isinstance(raw_w, (int, str)):
            w_frac = Fraction(raw_w)
        elif isinstance(raw_w, float):
            w_frac = Fraction(str(raw_w))
        elif isinstance(raw_w, dict):
            w_frac = core.json_to_fraction(raw_w)
        else:
            w_frac = Fraction(1, 1)
        total_weighted_frac += Fraction(score) * w_frac
        total_weight_frac += w_frac

    composite_frac = (total_weighted_frac / total_weight_frac) if total_weight_frac > 0 else Fraction(0, 1)
    composite_score = float(composite_frac)
    normalized_10 = (composite_score / 4.0) * 10.0

    all_bars_passed = all(v == "pass" for v in bar_verdicts.values())
    if not all_bars_passed:
        failed_bars = [k for k, v in bar_verdicts.items() if v != "pass"]
        print("========================================")
        print("FOUNDATION EVALUATION FAILED BARS")
        print("========================================")
        print(f"Failed bars: {failed_bars}")
        print("Final Certification: FAILED")
        return 1

    # Enforce optional policy thresholds if configured
    policy_thresholds = policy.get("optional_thresholds")
    policy_errors = []
    threshold_results = []
    if policy_thresholds:
        min_pass_rate = policy_thresholds.get("min_checkpoint_pass_rate")
        if min_pass_rate is not None:
            min_rate_frac = core.json_to_fraction(min_pass_rate, "scoring_policy.optional_thresholds.min_checkpoint_pass_rate")
            # For this evaluated checkpoint: 1/1 if passed, 0/1 if failed
            cp_pass_frac = Fraction(1, 1) if (overall_verdict == "pass" and all_bars_passed and not hard_failures) else Fraction(0, 1)
            if cp_pass_frac < min_rate_frac:
                policy_errors.append(
                    f"Policy threshold unmet: checkpoint pass rate {cp_pass_frac} < required minimum {min_rate_frac}"
                )
            threshold_results.append((f"min_checkpoint_pass_rate ({min_rate_frac})", "PASSED" if cp_pass_frac >= min_rate_frac else "FAILED"))

        min_traj_util = policy_thresholds.get("min_trajectory_utility")
        if min_traj_util is not None:
            min_util_frac = core.json_to_fraction(min_traj_util, "scoring_policy.optional_thresholds.min_trajectory_utility")
            if composite_frac < min_util_frac:
                policy_errors.append(
                    f"Policy threshold unmet: composite rating {composite_frac} ({composite_score:.4f}) < required minimum {min_util_frac} ({float(min_util_frac):.4f})"
                )
            threshold_results.append((f"min_trajectory_utility ({min_util_frac})", "PASSED" if composite_frac >= min_util_frac else "FAILED"))

    if policy_errors:
        print("========================================")
        print("FOUNDATION EVALUATION POLICY VIOLATIONS")
        print("========================================")
        for err in policy_errors:
            print(f"  [ERROR] {err}")
        print("----------------------------------------")
        print("Final Certification: FAILED (policy threshold not met)")
        return 1

    cp_weight = core.json_to_fraction(policy["checkpoint_weights"][cp_id], f"scoring_policy.checkpoint_weights.{cp_id}")

    print("========================================")
    print(f"FOUNDATION EVALUATION SCORECARD ({cp_id})")
    print("========================================")
    for dim_id, score in scores_by_dim.items():
        w = rubric_dims[dim_id].get("weight", 1.0)
        print(f"  {dim_id:<35}: {score:.1f}/4.0 (weight {w})")
    print("----------------------------------------")
    print(f"Composite Rating (0-4):  {composite_score:.2f} / 4.00")
    print(f"Normalized Score (0-10): {normalized_10:.2f} / 10.00")
    print(f"Policy Enforced:         {policy.get('policy_id', 'canonical')} (CP weight: {cp_weight})")
    if threshold_results:
        print("Policy Thresholds:")
        for t_name, t_res in threshold_results:
            print(f"  {t_name:<35}: {t_res}")

    print("\nBar Evidence Evaluation:")
    for b_id, verdict in bar_verdicts.items():
        print(f"  {b_id:<35}: {verdict.upper()}")

    print("\nOverall Verdict: PASS")
    print("Final Certification: CERTIFIED")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="repo-foundation Multi-Checkpoint Evaluation Harness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # validate
    sub_val = subparsers.add_parser("validate", help="Validate evaluation schemas and rubric")

    # snapshot
    sub_snap = subparsers.add_parser("snapshot", help="Take deterministic byte snapshot of a directory")
    sub_snap.add_argument("dir", help="Directory to snapshot")
    sub_snap.add_argument("--label", help="Optional snapshot label")
    sub_snap.add_argument("--out", help="Optional output JSON or directory path")

    # verify
    sub_ver = subparsers.add_parser("verify", help="Execute trusted checks for a checkpoint")
    sub_ver.add_argument("checkpoint", help="Checkpoint ID (e.g. CP1_BOOTSTRAP, CP2_SLICE, CP3_EVOLUTION, CP4_CONTINUITY)")
    sub_ver.add_argument("workspace", help="Path to workspace directory to test")
    sub_ver.add_argument("--timeout", type=int, default=30, help="Check timeout in seconds")

    # score
    sub_score = subparsers.add_parser("score", help="Compute score report from canonical judgment-v1 and rubric")
    sub_score.add_argument("--judgment", required=True, help="Path to judgment.json")
    sub_score.add_argument("--checkpoint", choices=["CP1_BOOTSTRAP", "CP2_SLICE", "CP3_EVOLUTION", "CP4_CONTINUITY"], help="Milestone checkpoint ID")
    sub_score.add_argument("--rubric", help="Optional path to custom rubric.json")
    sub_score.add_argument("--policy", help="Optional path to custom scoring_policy.json")

    args = parser.parse_args()

    if args.command == "validate":
        return cmd_validate(args)
    elif args.command == "snapshot":
        return cmd_snapshot(args)
    elif args.command == "verify":
        return cmd_verify(args)
    elif args.command == "score":
        return cmd_score(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
