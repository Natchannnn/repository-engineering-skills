import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Sequence

LEDGER_FILE = "ledger.jsonl"
_MODULE_DIR = Path(__file__).resolve().parent
_CSV_HEADER = ("id", "kind", "tenant", "payload")
_EXPORT_FIELDS = {"id", "kind", "tenant"}


def _ledger_path() -> Path:
    return _MODULE_DIR / LEDGER_FILE


def _read_records(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as ledger:
        return [json.loads(line) for line in ledger if line.strip()]


def _filtered_records(path: Path, tenant: str) -> list[dict]:
    return [
        record
        for record in _read_records(path)
        if record.get("tenant") == tenant
    ]


def _payload(record: dict) -> str:
    payload = {
        key: value
        for key, value in record.items()
        if key not in _EXPORT_FIELDS
    }
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _write_csv(records: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(_CSV_HEADER)
        for record in sorted(records, key=lambda item: item["id"]):
            writer.writerow(
                (
                    record["id"],
                    record["kind"],
                    record["tenant"],
                    _payload(record),
                )
            )


def _write_json(records: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8") as output:
        json.dump(
            records,
            output,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        output.write("\n")


def _print_summary(records: list[dict]) -> None:
    counts = Counter(record["kind"] for record in records)
    for kind in sorted(counts):
        print(f"kind:{kind} count:{counts[kind]}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--format", required=True, choices=("csv", "json"))
    parser.add_argument("--out", required=True)
    parser.add_argument("--summary", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    ledger_path = _ledger_path()
    if not ledger_path.is_file():
        print(f"error: {LEDGER_FILE} not found", file=sys.stderr)
        return 2

    try:
        records = _filtered_records(ledger_path, args.tenant)
        output_path = Path(args.out)
        if args.format == "csv":
            _write_csv(records, output_path)
        else:
            _write_json(records, output_path)
    except (OSError, TypeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if args.summary:
        _print_summary(records)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
