import json
import os
import tempfile
from pathlib import Path

LEDGER_FILE = "ledger.jsonl"
_MODULE_DIR = Path(__file__).resolve().parent


def _ledger_path() -> Path:
    configured_path = Path(LEDGER_FILE)
    if configured_path.is_absolute():
        return configured_path
    return _MODULE_DIR / configured_path


def read_all() -> list[dict]:
    path = _ledger_path()
    try:
        with path.open("r", encoding="utf-8") as ledger:
            return [json.loads(line) for line in ledger if line.strip()]
    except FileNotFoundError:
        return []


def append(event: dict) -> int:
    if not isinstance(event, dict):
        raise TypeError("event must be a dict")
    if "kind" not in event:
        raise ValueError("event must contain kind")
    kind = event["kind"]
    if not isinstance(kind, str):
        raise TypeError("event kind must be a string")
    if not kind.strip():
        raise ValueError("event kind must not be blank")

    next_id = len(read_all()) + 1
    record = {"id": next_id, **event}
    record["id"] = next_id
    record_bytes = (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")

    path = _ledger_path()
    existing_bytes = path.read_bytes() if path.exists() else b""
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = temporary_file.name
            temporary_file.write(existing_bytes)
            if existing_bytes and not existing_bytes.endswith((b"\n", b"\r")):
                temporary_file.write(b"\n")
            temporary_file.write(record_bytes)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass

    return next_id
