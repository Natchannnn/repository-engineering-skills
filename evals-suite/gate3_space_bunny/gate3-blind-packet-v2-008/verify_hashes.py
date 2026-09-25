"""Read-only reproduction of snapshot tree hashes in this packet."""

from hashlib import sha256
from pathlib import Path


PACKET = Path(__file__).resolve().parent
EXPECTED = {
    "predecessor": "c565d2dc8025b93c1b68e8e4d56bf39dcb3088fe4a43f2b14cf38e292177c5f4",
    "submitted": "ae8096188a532e2785cb52b18ce1bc0052231e91d84416c53588772cca757415",
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
