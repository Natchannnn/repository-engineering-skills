import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Sequence

LEDGER_FILE = "ledger.jsonl"
CSV_HEADER = ("id", "kind", "tenant", "payload")


def _ledger_path() -> Path:
    return Path(__file__).resolve().parent / LEDGER_FILE


def _read_records(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as ledger:
        return [json.loads(line) for line in ledger if line.strip()]


def _payload(record: dict) -> str:
    payload = {
        key: value
        for key, value in record.items()
        if key not in {"id", "kind", "tenant"}
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _write_csv(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(CSV_HEADER)
        for record in sorted(records, key=lambda item: item["id"]):
            writer.writerow(
                (record["id"], record["kind"], record["tenant"], _payload(record))
            )


def _write_json(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as output:
        json.dump(records, output, ensure_ascii=False)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--format", required=True, choices=("csv", "json"))
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--summary", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    ledger_path = _ledger_path()
    try:
        records = _read_records(ledger_path)
    except FileNotFoundError:
        print(f"error: ledger file not found: {ledger_path}", file=sys.stderr)
        return 2

    filtered_records = [
        record for record in records if record.get("tenant") == args.tenant
    ]

    if args.format == "csv":
        _write_csv(args.out, filtered_records)
    else:
        _write_json(args.out, filtered_records)

    if args.summary:
        counts = Counter(record["kind"] for record in filtered_records)
        for kind in sorted(counts):
            print(f"kind:{kind} count:{counts[kind]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
