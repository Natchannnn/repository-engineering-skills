"""Read-only byte-hash reproduction for this blind packet."""

from hashlib import sha256
from pathlib import Path


PACKET = Path(__file__).resolve().parent
EXPECTED = {
    "predecessor": "77486d97cb1facc0b62e3a3a4b455639da69d8736666167726380d96b7a5f4dd",
    "submitted": "4e5e84380b4e13d1063e0af8095e362fef63f7b8a5a37b135cd4786a6ff9edcd",
}


def tree_hash(root: Path) -> str:
    outer = sha256()
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"Unsupported packet entry: {path}")
        outer.update(path.relative_to(root).as_posix().encode("utf-8"))
        outer.update(b"\x00")
        outer.update(b"-")
        outer.update(sha256(path.read_bytes()).digest())
    return outer.hexdigest()


if __name__ == "__main__":
    for name, expected in EXPECTED.items():
        actual = tree_hash(PACKET / name)
        print(f"{name}: {actual}")
        if actual != expected:
            raise SystemExit(f"MISMATCH: {name}")
    actual_query = sha256((PACKET / "submitted" / "query.py").read_bytes()).hexdigest()
    print(f"submitted/query.py: {actual_query}")
    if actual_query != "1cc91e6d9fe8dfb31e026478a5a93161c07bfddf05a8ddc603119c9ab00c6558":
        raise SystemExit("MISMATCH: submitted/query.py")
