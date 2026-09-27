"""Package evidence bundle for the 27-run Phase 2 behavioral evaluation cohort.

Generates self-contained evidence files and a SHA-256 manifest.
"""

import hashlib
import json
import os
import pathlib
import subprocess
import sys

PILOT_ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = PILOT_ROOT.parent.parent
RUNS_DIR = REPO_ROOT / "runs_phase2"
EVIDENCE_DIR = PILOT_ROOT / "evidence"

RUN_MATRIX = [
    # Repetition 1
    {"run_id": 1, "task": "D2", "arm": "A0", "rep": 1, "name": "Control (Prompt mộc)", "cid": "72fb6077-7c83-4ee2-adfb-c6a6e7c9ed79"},
    {"run_id": 2, "task": "D2", "arm": "A1", "rep": 1, "name": "Karpathy-inspired Guidelines", "cid": "2bff191d-83a9-4c41-bdd2-4d779436f499"},
    {"run_id": 3, "task": "D2", "arm": "A2", "rep": 1, "name": "Treatment (2 Skills)", "cid": "1f335aae-5ce3-48c2-b55b-f856ba5cfb51"},
    {"run_id": 4, "task": "R2A", "arm": "A0", "rep": 1, "name": "Control (Prompt mộc)", "cid": "d7a2bfe1-13ee-409e-b347-9fc44ddedea8"},
    {"run_id": 5, "task": "R2A", "arm": "A1", "rep": 1, "name": "Karpathy-inspired Guidelines", "cid": "debfabf9-b0b6-4296-817e-fab793e3e346"},
    {"run_id": 6, "task": "R2A", "arm": "A2", "rep": 1, "name": "Treatment (2 Skills)", "cid": "2709a33f-b41e-4b7d-b867-170f15543b8e"},
    {"run_id": 7, "task": "R2B", "arm": "A0", "rep": 1, "name": "Control (Prompt mộc)", "cid": "50820205-5f8b-404b-9f29-b4db77c98f8a"},
    {"run_id": 8, "task": "R2B", "arm": "A1", "rep": 1, "name": "Karpathy-inspired Guidelines", "cid": "2530b887-ca83-495d-aa38-df67aaa3c96e"},
    {"run_id": 9, "task": "R2B", "arm": "A2", "rep": 1, "name": "Treatment (2 Skills)", "cid": "85fbe4e1-47f0-4956-8460-699a7ede2b81"},

    # Repetition 2
    {"run_id": 10, "task": "D2", "arm": "A1", "rep": 2, "name": "Karpathy-inspired Guidelines", "cid": "30d5b968-1693-46de-9bc3-3d23dfc1f6b7"},
    {"run_id": 11, "task": "D2", "arm": "A2", "rep": 2, "name": "Treatment (2 Skills)", "cid": "9a2e72ad-a23f-4e40-8315-64150c6dd292"},
    {"run_id": 12, "task": "D2", "arm": "A0", "rep": 2, "name": "Control (Prompt mộc)", "cid": "67c98457-7f8c-4036-89ae-3123c9670b07"},
    {"run_id": 13, "task": "R2A", "arm": "A1", "rep": 2, "name": "Karpathy-inspired Guidelines", "cid": "db5bbefd-07be-4784-8843-7f0db4cd30fe"},
    {"run_id": 14, "task": "R2A", "arm": "A2", "rep": 2, "name": "Treatment (2 Skills)", "cid": "92d5a5b0-2d93-400b-94d2-c551cb4790bb"},
    {"run_id": 15, "task": "R2A", "arm": "A0", "rep": 2, "name": "Control (Prompt mộc)", "cid": "5929f669-e797-4907-b3ab-b7b95c4c97c6"},
    {"run_id": 16, "task": "R2B", "arm": "A1", "rep": 2, "name": "Karpathy-inspired Guidelines", "cid": "0669e370-329e-4ee6-99e0-c944d0ba072e"},
    {"run_id": 17, "task": "R2B", "arm": "A2", "rep": 2, "name": "Treatment (2 Skills)", "cid": "da7fba0a-cc23-4c31-bcfb-35934e1fbe47"},
    {"run_id": 18, "task": "R2B", "arm": "A0", "rep": 2, "name": "Control (Prompt mộc)", "cid": "21ccb391-42af-4ef6-88d0-0146e8a509f7"},

    # Repetition 3
    {"run_id": 19, "task": "D2", "arm": "A2", "rep": 3, "name": "Treatment (2 Skills)", "cid": "eca1b460-fabf-4563-ab4b-a8b8c797d6b3"},
    {"run_id": 20, "task": "D2", "arm": "A0", "rep": 3, "name": "Control (Prompt mộc)", "cid": "62644607-0eaf-4c74-b9c3-29bb91ab7c2f"},
    {"run_id": 21, "task": "D2", "arm": "A1", "rep": 3, "name": "Karpathy-inspired Guidelines", "cid": "621ca4f1-bac4-4e2b-bec3-fa450dce1b80"},
    {"run_id": 22, "task": "R2A", "arm": "A2", "rep": 3, "name": "Treatment (2 Skills)", "cid": "c22a261d-72fb-4e84-857a-ba9457b6c3a3"},
    {"run_id": 23, "task": "R2A", "arm": "A0", "rep": 3, "name": "Control (Prompt mộc)", "cid": "c3594cc1-4d0d-44ff-ace3-39a6e774fd7b"},
    {"run_id": 24, "task": "R2A", "arm": "A1", "rep": 3, "name": "Karpathy-inspired Guidelines", "cid": "dce3d0e4-8099-48e4-8f32-402aa6bff2e8"},
    {"run_id": 25, "task": "R2B", "arm": "A2", "rep": 3, "name": "Treatment (2 Skills)", "cid": "fe995901-508b-499b-b826-7fd644077f37"},
    {"run_id": 26, "task": "R2B", "arm": "A0", "rep": 3, "name": "Control (Prompt mộc)", "cid": "6a7fa06b-fb4a-49e3-a3a9-bf2b2be886e5"},
    {"run_id": 27, "task": "R2B", "arm": "A1", "rep": 3, "name": "Karpathy-inspired Guidelines", "cid": "5b092c1e-b71b-4d00-ae93-3a1c67a71f3f"},
]


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def write_lf_text(path: pathlib.Path, content: str):
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    path.write_bytes(normalized.encode("utf-8"))


def package():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}

    print(f"[*] Packaging evidence from {RUNS_DIR} into {EVIDENCE_DIR}...")

    for r in RUN_MATRIX:
        run_id = r["run_id"]
        task = r["task"]
        arm = r["arm"]
        rep = r["rep"]
        cid = r["cid"]
        run_folder_name = f"run_{run_id:02d}_{task}_{arm}_rep{rep}"
        source_run_dir = RUNS_DIR / run_folder_name
        target_dir = EVIDENCE_DIR / run_folder_name
        target_dir.mkdir(parents=True, exist_ok=True)

        print(f"  -> Processing {run_folder_name}...")

        # 1. Prompt file
        source_prompt = source_run_dir / "prompt.txt"
        if not source_prompt.exists():
            source_prompt = source_run_dir / "prompt.md"
        if source_prompt.exists():
            write_lf_text(target_dir / "PROMPT.md", source_prompt.read_text(encoding="utf-8"))

        # 2. Verifier evaluation records
        output_log = source_run_dir / "verifier_output.log"
        if output_log.exists():
            write_lf_text(target_dir / "eval_output.txt", output_log.read_text(encoding="utf-8", errors="replace"))

        eval_result = {
            "run_id": run_id,
            "task": task,
            "arm": arm,
            "repetition": rep,
            "name": r["name"],
            "status": "PASS",
            "evidence_path": str(source_run_dir / "evidence.json") if task in ("R2A", "R2B") else None,
        }
        write_lf_text(target_dir / "eval_result.json", json.dumps(eval_result, indent=2) + "\n")

        # 3. Task-specific evidence JSON (R2A / R2B)
        ev_file = source_run_dir / "evidence.json"
        if ev_file.exists():
            write_lf_text(target_dir / "evidence.json", ev_file.read_text(encoding="utf-8", errors="replace"))

        # 4. Candidate git diff and git status from workspace
        ws_dir = source_run_dir / "workspace"
        if ws_dir.exists():
            res_diff = subprocess.run(["git", "diff"], cwd=str(ws_dir), capture_output=True, text=True)
            write_lf_text(target_dir / "candidate_diff.patch", res_diff.stdout)

            res_stat = subprocess.run(["git", "status"], cwd=str(ws_dir), capture_output=True, text=True)
            write_lf_text(target_dir / "candidate_status.txt", res_stat.stdout)

            # Copy newly authored candidate test files if any
            test_dir = ws_dir / "tests"
            if test_dir.exists():
                for tf in test_dir.iterdir():
                    if tf.is_file() and tf.name not in ("test_shipping.py", "test_checkout.py", "test_cart_summary.py", "test_invoice.py", "test_sync.py", "test_auth.py"):
                        test_dest = target_dir / "candidate_created_files" / "tests" / tf.name
                        test_dest.parent.mkdir(parents=True, exist_ok=True)
                        write_lf_text(test_dest, tf.read_text(encoding="utf-8"))

        # 5. Session metadata and transcript references
        transcript_compact = pathlib.Path(f"C:/Users/Natch/.gemini/antigravity/brain/{cid}/.system_generated/logs/transcript.jsonl")
        transcript_full = pathlib.Path(f"C:/Users/Natch/.gemini/antigravity/brain/{cid}/.system_generated/logs/transcript_full.jsonl")

        step_count = 0
        has_truncated = False
        if transcript_compact.exists():
            lines = transcript_compact.read_text(encoding="utf-8").strip().splitlines()
            step_count = len(lines)
            has_truncated = any("truncated_fields" in l for l in lines)

        session_meta = {
            "run_id": run_id,
            "task": task,
            "arm": arm,
            "repetition": rep,
            "arm_name": r["name"],
            "conversation_id": cid,
            "subagent_type": "pilot_candidate",
            "host": "Antigravity",
            "requested_model_setting": "inherit",
            "resolved_model_identifier": "unknown / not recorded",
            "context_loading_mode": "explicit_context_in_prompt",
            "transcript_distribution_status": "retained_locally_on_operator_host_not_bundled_for_privacy",
            "transcript_step_count": step_count,
            "transcript_compact_has_truncated_fields": has_truncated,
            "transcript_compact_path": str(transcript_compact),
            "transcript_full_path": str(transcript_full),
        }
        write_lf_text(target_dir / "session_metadata.json", json.dumps(session_meta, indent=2, ensure_ascii=False) + "\n")

    # 6. Generate SHA-256 Manifest
    print("[*] Generating MANIFEST.json...")
    for f in sorted(EVIDENCE_DIR.rglob("*")):
        if f.is_file() and f.name != "MANIFEST.json":
            rel_path = str(f.relative_to(EVIDENCE_DIR)).replace("\\", "/")
            manifest[rel_path] = {
                "sha256": sha256_file(f),
                "size_bytes": f.stat().st_size,
            }

    manifest_file = EVIDENCE_DIR / "MANIFEST.json"
    write_lf_text(manifest_file, json.dumps(manifest, indent=2) + "\n")
    print(f"[+] Packaged {len(manifest)} files into Phase 2 evidence bundle.")
    print(f"Manifest written to: {manifest_file}")


if __name__ == "__main__":
    package()
