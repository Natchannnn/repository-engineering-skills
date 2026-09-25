import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Sequence


LEDGER_FILE = Path(__file__).resolve().with_name("ledger.jsonl")
CSV_HEADER = ("id", "kind", "tenant", "payload")
RESERVED_FIELDS = {"id", "kind", "tenant"}


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--format", required=True, choices=("csv", "json"))
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--summary", action="store_true")
    return parser.parse_args(argv)


def _read_ledger(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as ledger_file:
        return [json.loads(line) for line in ledger_file if line.strip()]


def _filter_by_tenant(records: list[dict], tenant: str) -> list[dict]:
    return [record for record in records if record.get("tenant") == tenant]


def _encode_payload(record: dict) -> str:
    payload = {
        key: value for key, value in record.items() if key not in RESERVED_FIELDS
    }
    return json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _write_csv(records: list[dict], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.writer(output_file, lineterminator="\n")
        writer.writerow(CSV_HEADER)
        for record in sorted(records, key=lambda item: item["id"]):
            writer.writerow(
                (
                    record["id"],
                    record["kind"],
                    record["tenant"],
                    _encode_payload(record),
                )
            )


def _write_json(records: list[dict], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(records, output_file, ensure_ascii=False, allow_nan=False)
        output_file.write("\n")


def _print_summary(records: list[dict]) -> None:
    counts = Counter(record["kind"] for record in records)
    for kind in sorted(counts):
        print(f"kind:{kind} count:{counts[kind]}")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        records = _read_ledger(LEDGER_FILE)
    except FileNotFoundError:
        print(f"error: ledger not found: {LEDGER_FILE}", file=sys.stderr)
        return 2
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"error: unable to read ledger: {error}", file=sys.stderr)
        return 2

    filtered_records = _filter_by_tenant(records, args.tenant)

    try:
        if args.format == "csv":
            _write_csv(filtered_records, args.out)
        else:
            _write_json(filtered_records, args.out)
    except (OSError, UnicodeError, TypeError, ValueError) as error:
        print(f"error: unable to write export: {error}", file=sys.stderr)
        return 2

    if args.summary:
        _print_summary(filtered_records)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
