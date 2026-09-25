"""Read-only reproduction of snapshot tree hashes in this packet."""

from hashlib import sha256
from pathlib import Path


PACKET = Path(__file__).resolve().parent
EXPECTED = {
    "predecessor": "d229d032d51a1af855cc9bacd6fbef57def5e78cf80021ba12842b286a474956",
    "submitted": "636a98cea2479dd4fe81fbb58d7ebc3eb2f4fba4d6fee31c74b6e7021b6a4cd8",
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
