"""Read-only reproduction of snapshot tree hashes in this packet."""

from hashlib import sha256
from pathlib import Path


PACKET = Path(__file__).resolve().parent
EXPECTED = {
    "predecessor": "ace6956f9d1fcfc05c35a247f1466ac27c080f4c7a6d35b819742c442d59e648",
    "submitted": "143e2efb4f44c7327bf070f7e480245321016834e6b8bf37d4b25130521f98b0",
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
