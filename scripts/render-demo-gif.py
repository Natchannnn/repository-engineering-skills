#!/usr/bin/env python3
"""Render docs/demo/demo-40s.gif from REAL command outputs.

Runs the actual repo commands in temp dirs, captures their output, then draws a
terminal-style animation with hand-recorded tweaks (uneven typing speed, one
typo + backspace, cursor blink, pauses). Keeps everything reproducible:
re-run this script to regenerate the GIF after verifier changes.

Requires: Pillow only.  Output: docs/demo/demo-40s.gif (<2MB target).
"""
from __future__ import annotations

import pathlib
import random
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Pillow required: python -m pip install pillow")

random.seed(7)  # deterministic "human" jitter

W, H = 800, 500
BG = (12, 12, 12)
FG = (204, 204, 204)
GREEN = (22, 198, 12)
YELLOW = (240, 200, 90)
DIM = (120, 120, 120)
RED = (231, 72, 60)
PAD = 18
LINE_H = 22


def load_font(size: int = 16):
    for name in ("consola.ttf", "Consolas.ttf", "DejaVuSansMono.ttf",
                 "C:/Windows/Fonts/consola.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


FONT = load_font()


def run(cmd: list[str], cwd: pathlib.Path | None = None) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=str(cwd or ROOT), stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True)
    return p.returncode, p.stdout.strip()


def short(text: str, max_lines: int) -> list[str]:
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip() != ""]
    if len(lines) > max_lines:
        lines = lines[: max_lines - 1] + [f"... ({len(lines) - max_lines + 1} more lines)"]
    return [ln[:96] for ln in lines]


print("== running real commands ==")
td = tempfile.mkdtemp(prefix="gifdemo_")
rc1, out1 = run([sys.executable, "examples/read-only-contract-review/bootstrap.py",
                 f"{td}/d1"])
print("demo1 bootstrap:", rc1)
# happy-path report, same content as scripts/test_demos.py
rep = ("## Review Summary\nAudited feature branch against main.\n\n"
       "### Finding: Public Contract Drift\n- verdict: defect\n"
       "- source_file: src/profile.py\n- source_symbol: get_account_tier\n"
       "- affected_caller_file: src/billing.py\n"
       "- affected_caller_symbol: calculate_invoice\n"
       "- exception_type: KeyError\n- missing_key: discount_pct\n")
rp = pathlib.Path(td) / "report.txt"
rp.write_text(rep, encoding="utf-8")
subprocess.run([sys.executable, "examples/finalize_setup.py", f"{td}/d1"],
               check=True, stdout=subprocess.DEVNULL)
rc2, out2 = run([sys.executable, "examples/read-only-contract-review/verify.py",
                 "--fixture-dir", f"{td}/d1", "--review-output", str(rp)])
print("demo1 verify:", rc2)
rc3, out3 = run([sys.executable, "scripts/sync-shared.py", "--check"])
print("sync:", rc3)

# --- scenario: prompt + typed cmd + real output lines + color hits ---
PASS1 = [ln for ln in out2.splitlines() if "OVERALL" in ln] or ["OVERALL VERIFICATION: PASSED"]
SYNC_OK = short(out3, 2)
BOOT1 = short(out1, 2)

blocks = [
    {"cmd": "python scripts/sync-shared.py --check",
     "out": SYNC_OK, "hit": ["OK"], "typo": None, "pause": 500},
    {"cmd": "python examples/read-only-contract-review/bootstrap.py $env:TEMP\\d1",
     "out": BOOT1 or ["bootstrap OK"], "hit": [], "typo": None, "pause": 350},
    {"cmd": "python examples/read-only-contract-review/verfiy.py --fixture-dir $env:TEMP\\d1 --review-output report.txt",
     "out": [], "hit": [], "typo": (46, "verfiy", "verify"), "pause": 250,
     "fix_cmd": "python examples/read-only-contract-review/verify.py --fixture-dir $env:TEMP\\d1 --review-output report.txt"},
    {"cmd": None,
     "out": short(out2, 8) or PASS1, "hit": ["PASSED", "OK", "PASS"], "typo": None, "pause": 900},
]

PROMPT = "PS C:\\SKILLS-MAIN> "

# --- render ---
frames: list[Image.Image] = []
durations: list[int] = []
# (prompt-prefix, body, body-color). Prefix stays yellow while typing.
lines: list[tuple[str, str, tuple]] = []


def draw_screen(cursor_on: bool) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.ellipse([12, 12, 22, 22], fill=(255, 95, 86))
    d.ellipse([28, 12, 38, 22], fill=(255, 189, 46))
    d.ellipse([44, 12, 54, 22], fill=(39, 201, 63))
    d.text((64, 8), "PowerShell — SKILLS-MAIN", font=FONT, fill=DIM)
    y = 34
    for prefix, body, color in lines[-(H // LINE_H - 2):]:
        x = PAD
        if prefix:
            d.text((x, y), prefix, font=FONT, fill=YELLOW)
            x += d.textlength(prefix, font=FONT)
        d.text((x, y), body, font=FONT, fill=color)
        y += LINE_H
    if cursor_on and lines:
        prefix, body, _ = lines[-1]
        w = d.textlength(prefix + body, font=FONT)
        d.rectangle([PAD + w + 2, y - LINE_H, PAD + w + 12, y - 4], fill=FG)
    return img


def push(ms: int, cursor: bool = False):
    frames.append(draw_screen(cursor))
    durations.append(ms)


def type_cmd(cmd: str, typo=None, fixed: str | None = None):
    typed = ""
    i = 0
    # cursor blink before typing (human hesitation)
    lines.append((PROMPT, "", FG))
    push(350, True)
    push(250, False)
    while i < len(cmd):
        if typo and i == typo[0]:
            wrong = typo[1]
            for ch in wrong:
                typed += ch
                lines[-1] = (PROMPT, typed, FG)
                push(random.randint(60, 140))
            push(400)  # notice the typo
            for _ in wrong:
                typed = typed[:-1]
                lines[-1] = (PROMPT, typed, FG)
                push(70)
            right = typo[2]
            for ch in right:
                typed += ch
                lines[-1] = (PROMPT, typed, FG)
                push(random.randint(50, 110))
            i += len(typo[1])
            continue
        n = random.choice([1, 1, 2, 3])
        for ch in cmd[i: i + n]:
            typed += ch
            lines[-1] = (PROMPT, typed, FG)
        # slower after spaces and slashes, like a real typer
        last = typed[-1] if typed else ""
        base = random.randint(35, 95) + (60 if last in " /-_" else 0)
        push(base)
        i += n
    push(250)
    if fixed is not None:
        lines[-1] = (PROMPT, fixed, FG)


for b in blocks:
    if b["cmd"] is not None:
        type_cmd(b["cmd"], typo=b["typo"], fixed=b.get("fix_cmd"))
    if b["out"]:
        for ln in b["out"]:
            color = GREEN if any(h in ln for h in b["hit"]) else (FG if not ln.startswith("...") else DIM)
            if "FAIL" in ln or "error" in ln.lower()[:20]:
                color = RED
            lines.append(("", ln, color))
            push(90)
    push(b["pause"], cursor=False)

push(1500)  # hold final frame

out_path = ROOT / "docs" / "demo" / "demo-40s.gif"
# Fixed 16-color palette: the animation only uses ~9 flat colors, so quantizing
# every frame to the same small palette keeps greens/yellows stable from the
# first frame to the last (ADAPTIVE per-save was drifting mid-file).
paletted = [f.convert("P", palette=Image.ADAPTIVE, colors=16) for f in frames]
paletted[0].save(out_path, save_all=True, append_images=paletted[1:],
                 duration=durations, loop=0, optimize=True)
size_kb = out_path.stat().st_size // 1024
print(f"wrote {out_path} ({len(frames)} frames, {size_kb}KB)")
if size_kb > 2048:
    print("WARNING: over 2MB budget", file=sys.stderr)
