"""Bounded CLI evaluation. Labels and verifiers stay outside runner workspaces."""

import argparse
import difflib
import hashlib
import json
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import check


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SETTINGS_ROOT = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
CLI = shutil.which("codex") or shutil.which("codex.exe") or "codex"
SKILLS = ("repo-foundation", "repo-native-refactor")
PROTOCOL = json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))
PROMPTS = {
    "migration": "Implement the approved account migration in README.md. Update the loader, callers, sample data, persistent tests and documentation to the target contract. Preserve the unrelated user fee edits. Verify success and failure behavior. Do not commit or push.",
    "review": "Review change.patch against baseline.py, app.py, README.md and callers. Report only evidence-backed defects with their file, symbol, evidence and consequence. Do not modify any project files. Do not commit or push.",
    "neither-en": "Explain the difference between a Python list and tuple in two short sentences. No repository work is requested.",
    "neither-vi": "Trong câu sau, thay 'sử dụng' bằng 'dùng' và chỉ trả về câu đã sửa: Bạn nên sử dụng tên rõ ràng.",
    "mixed": "Thêm tùy chọn include_count=True cho summarize(values), trả về dict có total và count. Giữ kết quả số nguyên hiện tại khi không bật tùy chọn, kể cả đầu vào rỗng và generator. Cập nhật test và README. Khi triển khai và kiểm tra xong, review phần thay đổi một lần để phát hiện lỗi hoặc sửa phần thừa có căn cứ. Không commit hoặc push.",
}
BOUNDARY = "\nWork only in this workspace and its installed .agents/skills. Do not read parent directories, evaluator files, other runs or prior results. No network, installations, delegation, commits or pushes. Use Python -B. Keep verification proportional to this small project; finish within 14 shell calls. Final summary under 160 words; findings must contain only actual defects."
SCHEMA = {"type": "object", "properties": {
    "summary": {"type": "string"},
    "findings": {"type": "array", "items": {"type": "object", "properties": {
        k: {"type": "string"} for k in ("file", "symbol", "evidence", "consequence")},
        "required": ["file", "symbol", "evidence", "consequence"], "additionalProperties": False}}},
    "required": ["summary", "findings"], "additionalProperties": False}


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def inventory(path, skills=False):
    return {f.relative_to(path).as_posix(): digest(f.read_bytes()) for f in sorted(path.rglob("*"))
            if f.is_file() and (skills or ".agents" not in f.relative_to(path).parts)
            and "__pycache__" not in f.parts}


def commands(workspace, profile):
    return [CLI, "--no-daemon", "exec", "--ignore-rules", "--ephemeral",
            "--skip-git-repo-check", "--json", "-C", str(workspace), "-p", profile,
            "-m", PROTOCOL["model"], "-c", 'model_reasoning_effort="low"',
            "-c", 'service_tier="default"', "-c", 'approval_policy="never"',
            "--disable", "apps", "--disable", "plugins", "--disable", "multi_agent",
            "--disable", "browser_use", "-s", "danger-full-access"]


def prepare(path):
    path.mkdir(parents=True, exist_ok=False)
    save(path / "protocol.json", PROTOCOL)
    save(path / "output-schema.json", SCHEMA)
    prior_summary = HERE / "excluded-run-summary.json"
    if prior_summary.exists():
        shutil.copy2(prior_summary, path / "excluded-run-summary.json")
    profile_name = "skills-budget-" + digest(str(path.resolve()).encode())[:12]
    profile_path = SETTINGS_ROOT / (profile_name + ".config.toml")
    if profile_path.exists():
        raise RuntimeError("Refusing to overwrite an existing CLI profile")
    host_roots = (Path.home() / ".agents/skills", SETTINGS_ROOT / "skills", SETTINGS_ROOT / "plugins/cache")
    manifests = sorted({f.resolve().as_posix() for r in host_roots for f in r.rglob("SKILL.md")})
    profile_bytes = ('[skills]\nconfig = [' + ','.join('{path = ' + json.dumps(f) +
                     ', enabled = false}' for f in manifests) + ']\n').encode()
    profile_path.write_bytes(profile_bytes)
    metadata = {"prepared_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "profile_name": profile_name, "profile_path": str(profile_path),
                "profile_sha256": digest(profile_bytes), "foreign_skills_disabled": len(manifests),
                "protocol_sha256": digest((path / "protocol.json").read_bytes()),
                "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "cli_version": subprocess.check_output([CLI, "--version"], text=True).strip(),
                "runtime_hashes": {name: inventory(ROOT / name / "references", True) | {
                    "SKILL.md": digest((ROOT / name / "SKILL.md").read_bytes()),
                    "agents/openai.yaml": digest((ROOT / name / "agents/openai.yaml").read_bytes())} for name in SKILLS}}
    save(path / "metadata.json", metadata)
    for run_id in PROTOCOL["run_order"]:
        case = path / run_id
        w = case / "workspace"
        family = run_id.split("-")[0]
        if family in ("migration", "review", "mixed"):
            shutil.copytree(HERE / "fixtures" / family, w)
        else:
            w.mkdir(parents=True)
        if family == "review":
            patch = difflib.unified_diff((w / "baseline.py").read_text().splitlines(True),
                                         (w / "app.py").read_text().splitlines(True), "baseline.py", "app.py")
            (w / "change.patch").write_text("".join(patch), encoding="utf-8")
        if "-control-" not in run_id:
            for name in SKILLS:
                target = w / ".agents/skills" / name
                target.mkdir(parents=True)
                shutil.copy2(ROOT / name / "SKILL.md", target / "SKILL.md")
                shutil.copytree(ROOT / name / "references", target / "references")
                shutil.copytree(ROOT / name / "agents", target / "agents")
        (case / "prompt.txt").write_text(PROMPTS.get(run_id, PROMPTS.get(family, "")) + BOUNDARY, encoding="utf-8")
        save(case / "before.json", inventory(w))
        save(case / "skills-before.json", inventory(w / ".agents", True))
        args = [CLI, "--no-daemon", "-p", profile_name, "-C", str(w), "-c", "features.apps=false",
                "-c", "features.plugins=false", "debug", "prompt-input", "catalog preflight"]
        r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", timeout=30)
        if r.returncode:
            raise RuntimeError(r.stderr)
        raw = json.loads(r.stdout)
        text = "\n".join(json.dumps(x, ensure_ascii=False) for x in raw)
        i = text.find("### Available skills")
        catalog = text[i:text.find("</skills_instructions>", i)] if i >= 0 else ""
        expected = [] if "-control-" in run_id else list(SKILLS)
        for name in SKILLS:
            assert (f"- {name}:" in catalog) == (name in expected), (run_id, name, catalog)
        lines = [x.strip() for x in catalog.replace("\\n", "\n").splitlines() if x.strip().startswith("- ")]
        assert len(lines) == len(expected), (run_id, lines)
        save(case / "catalog.json", {"catalog": catalog, "expected_names": expected,
                                    "debug_prompt_sha256": digest(r.stdout.encode())})
    print(json.dumps({"prepared": str(path), "sessions": len(PROTOCOL["run_order"]),
                      "foreign_skills_disabled": len(manifests)}, ensure_ascii=False))


def events(case):
    return [json.loads(line) for line in (case / "events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


def observe(case):
    ev = events(case)
    completed = [e["item"] for e in ev if e.get("type") == "item.completed"]
    shell = [i for i in completed if i.get("type") == "command_execution"]
    reads = []
    for index, item in enumerate(completed):
        if item.get("type") != "command_execution":
            continue
        output = item.get("aggregated_output", "").replace("\r\n", "\n")
        found = []
        for name in SKILLS:
            entry = (case / "workspace/.agents/skills" / name / "SKILL.md")
            if entry.exists():
                content = entry.read_text(encoding="utf-8").replace("\r\n", "\n").strip()
                if content in output:
                    found.append((output.index(content), name))
        for offset, name in sorted(found):
            reads.append({"skill": name, "completed_item_index": index, "command": item["command"],
                          "shell_exit_code": item.get("exit_code"),
                          "evidence": "full actual entrypoint content in captured command output"})
    usage = next((e["usage"] for e in ev if e.get("type") == "turn.completed"), None)
    final = json.loads((case / "final.json").read_text(encoding="utf-8")) if (case / "final.json").exists() else None
    return {"usage": usage, "completed_commands": len(shell), "skill_reads": reads, "final": final,
            "errors": [i.get("message") for i in completed if i.get("type") == "error"]}


def run(path, run_id):
    assert run_id in PROTOCOL["run_order"]
    case = path / run_id
    if (case / "events.jsonl").exists():
        raise RuntimeError("No replacement or retry of an existing trial")
    usage_records = []
    missing_usage = 0
    for log in list(path.glob("*/events.jsonl")) + list(path.parent.glob("calibration*/events.jsonl")):
        turn_complete = False
        for line in log.read_text(encoding="utf-8").splitlines():
            e = json.loads(line)
            if e.get("type") == "turn.completed":
                usage_records.append(e["usage"])
                turn_complete = True
        if not turn_complete:
            missing_usage += 1
    uncached = sum(u["input_tokens"] - u.get("cached_input_tokens", 0) for u in usage_records)
    output_tokens = sum(u["output_tokens"] for u in usage_records)
    accounted_input = uncached + missing_usage * PROTOCOL["budget"].get("missing_usage_input_reserve", 0)
    accounted_output = output_tokens + missing_usage * PROTOCOL["budget"].get("missing_usage_output_reserve", 0)
    prior_path = path / "excluded-run-summary.json"
    if prior_path.exists():
        prior = json.loads(prior_path.read_text(encoding="utf-8"))
        accounted_input += prior["measured_totals"]["uncached_input_tokens"] + prior["unavailable_usage_turns"] * PROTOCOL["budget"]["missing_usage_input_reserve"]
        accounted_output += prior["measured_totals"]["output_tokens"] + prior["unavailable_usage_turns"] * PROTOCOL["budget"]["missing_usage_output_reserve"]
    if accounted_input >= PROTOCOL["budget"]["stop_after_cumulative_uncached_input_tokens"] or accounted_output >= PROTOCOL["budget"]["stop_after_cumulative_output_tokens"]:
        raise RuntimeError(f"Budget reached before starting session: measured uncached={uncached}, output={output_tokens}, unavailable turns={missing_usage}")
    for family in PROTOCOL["matched_families"]:
        reports = [json.loads(f.read_text(encoding="utf-8")) for f in path.glob(f"{family}-skills-*/verification.json")]
        if len(reports) == 2:
            failed = [{k for k, v in r["checks"].items() if v is not True} for r in reports]
            if failed[0] & failed[1]:
                raise RuntimeError(f"Repeated treatment failure already disqualifies rating gate: {family}, {sorted(failed[0] & failed[1])}")
    meta = json.loads((path / "metadata.json").read_text())
    assert digest((path / "protocol.json").read_bytes()) == meta["protocol_sha256"]
    assert digest(Path(meta["profile_path"]).read_bytes()) == meta["profile_sha256"]
    args = commands(case / "workspace", meta["profile_name"]) + ["--output-schema", str(path / "output-schema.json"),
            "-o", str(case / "final.json"), "-"]
    save(case / "args.json", args)
    q = queue.Queue()
    start = time.monotonic()
    reason = None
    count = 0
    with (case / "stderr.txt").open("w", encoding="utf-8") as err, (case / "events.jsonl").open("w", encoding="utf-8") as out:
        child = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err,
                                 text=True, encoding="utf-8")
        child.stdin.write((case / "prompt.txt").read_text(encoding="utf-8"))
        child.stdin.close()

        def reader():
            for line in child.stdout:
                q.put(line)
            q.put(None)

        threading.Thread(target=reader, daemon=True).start()
        while True:
            if time.monotonic() - start > PROTOCOL["budget"]["seconds_per_session"]:
                reason = "time ceiling"
                child.kill()
                break
            try:
                line = q.get(timeout=0.5)
            except queue.Empty:
                continue
            if line is None:
                break
            out.write(line)
            out.flush()
            e = json.loads(line)
            if e.get("type") == "item.completed" and e.get("item", {}).get("type") == "command_execution":
                count += 1
                if count > PROTOCOL["budget"]["max_completed_commands_per_session"]:
                    reason = "command ceiling"
                    child.kill()
                    break
        child.wait(timeout=10)
    save(case / "execution.json", {"exit": child.returncode, "seconds": round(time.monotonic() - start, 2),
                                  "stop_reason": reason})
    info = observe(case)
    save(case / "observation.json", info)
    print(json.dumps({"run": run_id, "exit": child.returncode, "seconds": round(time.monotonic() - start, 2),
                      "usage": info["usage"], "commands": info["completed_commands"],
                      "reads": [r["skill"] for r in info["skill_reads"]], "stop": reason}, ensure_ascii=False))


def verify(path, run_id):
    case = path / run_id
    w = case / "workspace"
    family = run_id.split("-")[0]
    info = observe(case)
    results = {"completed_with_trace": info["usage"] is not None and not info["errors"],
               "runtime_unchanged": inventory(w / ".agents", True) == json.loads((case / "skills-before.json").read_text())}
    if family == "migration":
        results.update(check.migration(w, HERE / "fixtures/migration"))
    elif family == "review":
        findings = (info["final"] or {}).get("findings", [])
        results["project_unchanged"] = inventory(w) == json.loads((case / "before.json").read_text())
        results["exactly_one_supported_retry_finding"] = len(findings) == 1 and "publish_with_retry" in findings[0].get("symbol", "") and "app.py" in findings[0].get("file", "") and bool(findings[0].get("evidence")) and bool(findings[0].get("consequence"))
        # Independent execution proves the reported producer/consumer failure.
        m = check.module(w / "app.py")
        calls = []

        def fail(event, **kwargs):
            calls.append(kwargs)
            raise m.TransientError("temporary")

        results["retry_regression_independently_reproduced"] = m.publish_with_retry({"id": "ev-1"}, fail) is None and len(calls) == 3
    elif family == "mixed":
        try:
            results.update(check.mixed(w, HERE / "fixtures/mixed"))
        except Exception as exc:
            results["feature_default_generator_docs_tests"] = f"{type(exc).__name__}: {exc}"
    else:
        results["project_unchanged"] = inventory(w) == json.loads((case / "before.json").read_text())
        results["no_findings"] = (info["final"] or {}).get("findings") == []
    if family in ("migration", "mixed"):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "candidate"
            shutil.copytree(w, candidate, ignore=shutil.ignore_patterns(".agents", "__pycache__"))
            checked = check.tests(candidate)
            results["candidate_tests_pass"] = checked["exit"] == 0
            if family == "migration":
                results["persistent_tests_updated"] = (w / "test_ledger.py").read_bytes() != (HERE / "fixtures/migration/test_ledger.py").read_bytes() or len(list(w.glob("test*.py"))) > 1
            main = "ledger.py" if family == "migration" else "app.py"
            shutil.copy2(HERE / "fixtures" / family / main, candidate / main)
            original = check.tests(candidate)
            results["candidate_tests_reject_original"] = original["exit"] != 0
        info["test_execution"] = checked
        info["original_implementation_test_execution"] = original
    skill_names = [r["skill"] for r in info["skill_reads"]]
    if "-control-" in run_id:
        results["no_skill_read_in_control"] = not skill_names
    else:
        expected = PROTOCOL["expected_initial_skill"][family]
        results["initial_routing"] = (skill_names[0] if skill_names else None) == expected
        if family == "mixed":
            results["later_refactor_read"] = "repo-native-refactor" in skill_names[1:]
    report = {"run": run_id, "checks": results, "pass": all(v is True for v in results.values()), "observation": info,
              "after_hashes": inventory(w), "execution": json.loads((case / "execution.json").read_text())}
    save(case / "verification.json", report)
    print(json.dumps({"run": run_id, "pass": report["pass"], "failed": {k: v for k, v in results.items() if v is not True}}, ensure_ascii=False))


def cleanup(path):
    meta = json.loads((path / "metadata.json").read_text())
    profile = Path(meta["profile_path"])
    assert profile.parent.resolve() == SETTINGS_ROOT.resolve() and profile.name.startswith("skills-budget-")
    if profile.exists():
        assert digest(profile.read_bytes()) == meta["profile_sha256"]
        profile.unlink()
    print("Temporary CLI profile removed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "run", "verify", "cleanup"))
    parser.add_argument("run_root", type=Path)
    parser.add_argument("run_id", nargs="?")
    args = parser.parse_args()
    {"prepare": prepare, "cleanup": cleanup}[args.action](args.run_root) if args.action in ("prepare", "cleanup") else {"run": run, "verify": verify}[args.action](args.run_root, args.run_id)
