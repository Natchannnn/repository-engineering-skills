#!/usr/bin/env python3
"""
Bootstrap script for Task R2A (Neutral Review Fixture A).
Initializes a git repository with main branch and checkout on review/batch-sync-v2.
This fixture contains a clean, safe refactor where all callers are properly migrated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        raise RuntimeError(f"Command failed ({cmd}):\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")
    return res


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def bootstrap_r2a(target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)

    run_cmd(["git", "init", "-b", "main"], target_dir)
    run_cmd(["git", "config", "user.name", "Review Author"], target_dir)
    run_cmd(["git", "config", "user.email", "review-author@pilot.test"], target_dir)
    run_cmd(["git", "config", "commit.gpgsign", "false"], target_dir)

    src_dir = target_dir / "src"
    src_dir.mkdir(exist_ok=True)
    tests_dir = target_dir / "tests"
    tests_dir.mkdir(exist_ok=True)

    # 1. src/__init__.py
    (src_dir / "__init__.py").write_text("", encoding="utf-8")

    # 2. src/batch_sync.py on main
    batch_sync_v1 = '''"""Batch sync processing service."""
from __future__ import annotations


def sync_batch(items: list[dict], batch_id: str) -> int:
    """Synchronizes a batch of items and returns count of synced items."""
    if not items:
        return 0
    count = 0
    for item in items:
        if item.get("active", True):
            count += 1
    return count
'''
    (src_dir / "batch_sync.py").write_text(batch_sync_v1, encoding="utf-8")

    # 3. src/sync_worker.py on main
    sync_worker_v1 = '''"""Background worker for batch sync."""
from __future__ import annotations

from src.batch_sync import sync_batch


def process_queue(queue_items: list[dict], queue_id: str) -> int:
    """Processes queue items using batch sync."""
    return sync_batch(queue_items, queue_id)
'''
    (src_dir / "sync_worker.py").write_text(sync_worker_v1, encoding="utf-8")

    # 4. src/cron_jobs.py on main
    cron_jobs_v1 = '''"""Scheduled cron sync tasks."""
from __future__ import annotations

from src.batch_sync import sync_batch


def run_nightly_sync(records: list[dict]) -> int:
    """Nightly sync job."""
    return sync_batch(records, "nightly_sync")
'''
    (src_dir / "cron_jobs.py").write_text(cron_jobs_v1, encoding="utf-8")

    # 5. tests/__init__.py
    (tests_dir / "__init__.py").write_text("", encoding="utf-8")

    # 6. tests/test_sync.py
    test_sync = '''import unittest
from src.batch_sync import sync_batch
from src.sync_worker import process_queue
from src.cron_jobs import run_nightly_sync


class TestSync(unittest.TestCase):
    def test_sync_basic(self):
        items = [{"id": 1, "active": True}, {"id": 2, "active": False}]
        self.assertEqual(sync_batch(items, "b1"), 1)
        self.assertEqual(process_queue(items, "q1"), 1)
        self.assertEqual(run_nightly_sync(items), 1)


if __name__ == "__main__":
    unittest.main()
'''
    (tests_dir / "test_sync.py").write_text(test_sync, encoding="utf-8")

    # Commit main
    run_cmd(["git", "add", "."], target_dir)
    run_cmd(["git", "commit", "-m", "feat: baseline batch sync system"], target_dir)
    main_head = run_cmd(["git", "rev-parse", "HEAD"], target_dir).stdout.strip()

    # Create feature branch: review/batch-sync-v2
    run_cmd(["git", "checkout", "-b", "review/batch-sync-v2"], target_dir)

    # In feature branch: Refactor batch_sync with optional SyncOptions dataclass
    batch_sync_v2 = '''"""Batch sync processing service."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SyncOptions:
    chunk_size: int = 100
    dry_run: bool = False


def sync_batch(
    items: list[dict], batch_id: str, options: SyncOptions | None = None
) -> int:
    """Synchronizes a batch of items with optional chunking and dry-run."""
    if not items:
        return 0
    opts = options or SyncOptions()
    if opts.dry_run:
        return 0
    count = 0
    for item in items:
        if item.get("active", True):
            count += 1
    return count
'''
    (src_dir / "batch_sync.py").write_text(batch_sync_v2, encoding="utf-8")

    # Update cron_jobs.py to pass custom options
    cron_jobs_v2 = '''"""Scheduled cron sync tasks."""
from __future__ import annotations

from src.batch_sync import SyncOptions, sync_batch


def run_nightly_sync(records: list[dict]) -> int:
    """Nightly sync job with tuned chunk options."""
    options = SyncOptions(chunk_size=50)
    return sync_batch(records, "nightly_sync", options=options)
'''
    (src_dir / "cron_jobs.py").write_text(cron_jobs_v2, encoding="utf-8")

    # Note: sync_worker.py continues to call sync_batch(queue_items, queue_id) without options.
    # Because options has a default value (options: SyncOptions | None = None), this call remains 100% valid!

    run_cmd(["git", "add", "."], target_dir)
    run_cmd(["git", "commit", "-m", "refactor: add chunking options to sync_batch and update cron jobs"], target_dir)
    feature_head = run_cmd(["git", "rev-parse", "HEAD"], target_dir).stdout.strip()

    # Snapshot manifest of review branch
    manifest: dict[str, dict[str, int | str]] = {}
    for p in target_dir.rglob("*"):
        if p.is_file() and ".git" not in p.parts:
            rel = p.relative_to(target_dir).as_posix()
            manifest[rel] = {
                "sha256": compute_sha256(p),
                "size_bytes": p.stat().st_size,
            }

    snapshot_path = target_dir.parent / f"{target_dir.name}-r2a-snapshot.json"
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "main_head": main_head,
                "feature_head": feature_head,
                "branch": "review/batch-sync-v2",
                "manifest": manifest,
            },
            f,
            indent=2,
        )

    print(f"Successfully bootstrapped R2A fixture at: {target_dir}")
    print(f"MAIN_HEAD:        {main_head}")
    print(f"FEATURE_HEAD:     {feature_head} (review/batch-sync-v2)")
    print(f"Snapshot file:    {snapshot_path}")
    return target_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap Task R2A fixture")
    parser.add_argument("--target-dir", required=True, help="Path to bootstrap target directory")
    args = parser.parse_args()
    bootstrap_r2a(Path(args.target_dir).resolve())
