"""Check that each installable skill's own resources resolve in isolation."""

import re
import shutil
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("repo-foundation", "repo-native-refactor")


def check_resources(skill_root):
    skill_root = Path(skill_root).resolve()
    documents = [skill_root / "SKILL.md", *sorted((skill_root / "references").glob("*.md"))]
    for document in documents:
        text = document.read_text(encoding="utf-8")
        targets = re.findall(r"\[[^\]]*\]\(([^)]+)\)", text)
        targets += re.findall(r"\b(?:docs|scripts|evals)/(?:[\w.-]+/)*[\w.-]+\.(?:md|py|ps1|sh|json|yaml)\b", text)
        for target in targets:
            parsed = urlsplit(target)
            if parsed.scheme or not parsed.path:
                continue
            resolved = (document.parent / unquote(parsed.path)).resolve()
            if not resolved.is_relative_to(skill_root) or not resolved.is_file():
                raise ValueError(f"{document.relative_to(skill_root)}: unavailable skill resource {target}")


def copy_runtime(name, destination):
    source = ROOT / name
    destination.mkdir(parents=True)
    shutil.copy2(source / "SKILL.md", destination / "SKILL.md")
    shutil.copytree(source / "references", destination / "references")


class RuntimeResourceTest(unittest.TestCase):
    def test_each_skill_resolves_without_repository_source_or_companion(self):
        for name in SKILLS:
            with self.subTest(skill=name), tempfile.TemporaryDirectory() as directory:
                skill = Path(directory) / name
                copy_runtime(name, skill)
                check_resources(skill)

    def test_missing_link_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "repo-foundation"
            copy_runtime("repo-foundation", skill)
            (skill / "references" / "bootstrap.md").unlink()
            with self.assertRaisesRegex(ValueError, "bootstrap.md"):
                check_resources(skill)

    def test_missing_maintainer_script_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "repo-foundation"
            copy_runtime("repo-foundation", skill)
            with (skill / "references" / "shared-contracts.md").open("a", encoding="utf-8") as file:
                file.write("\nRun `python scripts/regenerate.py` before proceeding.\n")
            with self.assertRaisesRegex(ValueError, "scripts/regenerate.py"):
                check_resources(skill)


if __name__ == "__main__":
    unittest.main()
