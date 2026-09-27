"""Package evidence bundle for the 9-run behavioral pilot.

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
RUNS_DIR = REPO_ROOT / "runs"
EVIDENCE_DIR = PILOT_ROOT / "evidence"

RUN_MATRIX = [
    {"run_id": 1, "task": "D1", "arm": "A0", "name": "Control (Prompt mộc)", "cid": "a06f15a0-ff13-4eca-9f6d-7f8a662ba3f7"},
    {"run_id": 2, "task": "D1", "arm": "A1", "name": "Karpathy-inspired Guidelines", "cid": "4ecc2f7a-da31-43a0-b40f-e6e2a1c81716"},
    {"run_id": 3, "task": "D1", "arm": "A2", "name": "Treatment (2 Skills)", "cid": "79109407-4aa2-4463-b201-9fc31ffe9f91"},
    {"run_id": 4, "task": "D3", "arm": "A1", "name": "Karpathy-inspired Guidelines", "cid": "02c7940d-a842-48e6-8268-49c3b8c6d67e"},
    {"run_id": 5, "task": "D3", "arm": "A2", "name": "Treatment (2 Skills)", "cid": "4c380f28-e06e-432c-84dc-361664cf4326"},
    {"run_id": 6, "task": "D3", "arm": "A0", "name": "Control (Prompt mộc)", "cid": "30d63cb2-a220-474d-a1ba-593605c426ef"},
    {"run_id": 7, "task": "R1", "arm": "A2", "name": "Treatment (2 Skills)", "cid": "faccc14a-d0a4-413f-baf1-fd6b02faecce"},
    {"run_id": 8, "task": "R1", "arm": "A0", "name": "Control (Prompt mộc)", "cid": "05ecf963-6e6b-4d4a-85d1-ee2454bd48aa"},
    {"run_id": 9, "task": "R1", "arm": "A1", "name": "Karpathy-inspired Guidelines", "cid": "5a2d1040-7844-4189-bd40-dc20c75f5d26"},
]

def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def package():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}

    print(f"[*] Packaging evidence from {RUNS_DIR} into {EVIDENCE_DIR}...")

    for r in RUN_MATRIX:
        run_id = r["run_id"]
        task = r["task"]
        arm = r["arm"]
        cid = r["cid"]
        run_name = f"run_{run_id:02d}_{task}_{arm}"
        source_run_dir = RUNS_DIR / run_name
        target_dir = EVIDENCE_DIR / run_name
        target_dir.mkdir(parents=True, exist_ok=True)

        print(f"  -> Processing {run_name}...")

        # 1. Prompt file
        source_prompt = source_run_dir / "PROMPT_TO_PASTE.md"
        if source_prompt.exists():
            (target_dir / "PROMPT.md").write_text(source_prompt.read_text(encoding="utf-8"), encoding="utf-8")

        # 2. Verifier evaluation records
        for fn in ["eval_result.json", "eval_output.txt", "status_report.json", "evidence.json"]:
            s_file = source_run_dir / fn
            if s_file.exists():
                (target_dir / fn).write_bytes(s_file.read_bytes())

        # 3. Candidate git diff and git status from workspace
        ws_dir = source_run_dir / "workspace"
        if ws_dir.exists():
            # git diff
            res_diff = subprocess.run(["git", "diff"], cwd=str(ws_dir), capture_output=True, text=True)
            (target_dir / "candidate_diff.patch").write_text(res_diff.stdout, encoding="utf-8")

            # git status
            res_stat = subprocess.run(["git", "status"], cwd=str(ws_dir), capture_output=True, text=True)
            (target_dir / "candidate_status.txt").write_text(res_stat.stdout, encoding="utf-8")

            # Copy newly authored candidate test files if any
            for candidate_test in ["tests/test_order_normalization.py", "tests/test_quarterly_balance.py"]:
                tf = ws_dir / candidate_test
                if tf.exists():
                    test_dest = target_dir / "candidate_created_files" / candidate_test
                    test_dest.parent.mkdir(parents=True, exist_ok=True)
                    test_dest.write_text(tf.read_text(encoding="utf-8"), encoding="utf-8")

        # 4. Session metadata and transcript references
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
            "arm_name": r["name"],
            "conversation_id": cid,
            "subagent_type": "pilot_candidate",
            "model_identifier": "Google Antigravity Advanced Agentic Coding Engine (Gemini 2.5 architecture, Model: inherit)",
            "context_loading_mode": "explicit_context_in_prompt",
            "transcript_step_count": step_count,
            "transcript_compact_has_truncated_fields": has_truncated,
            "transcript_compact_path": str(transcript_compact),
            "transcript_full_path": str(transcript_full)
        }
        (target_dir / "session_metadata.json").write_text(json.dumps(session_meta, indent=2, ensure_ascii=False), encoding="utf-8")

    # Generate SHA-256 Manifest
    print("[*] Generating MANIFEST.json...")
    for f in sorted(EVIDENCE_DIR.rglob("*")):
        if f.is_file() and f.name != "MANIFEST.json":
            rel_path = str(f.relative_to(EVIDENCE_DIR)).replace("\\", "/")
            manifest[rel_path] = {
                "sha256": sha256_file(f),
                "size_bytes": f.stat().st_size
            }

    manifest_file = EVIDENCE_DIR / "MANIFEST.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[+] Packaged {len(manifest)} files into evidence bundle.")
    print(f"Manifest written to: {manifest_file}")

if __name__ == "__main__":
    package()
