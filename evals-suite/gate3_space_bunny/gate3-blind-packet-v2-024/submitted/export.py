import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path


LEDGER_FILE = Path(__file__).resolve().with_name("ledger.jsonl")
CSV_FIELDS = ["id", "kind", "tenant", "payload"]
RESERVED_FIELDS = {"id", "kind", "tenant"}


def _read_all() -> list[dict]:
    records = []
    with LEDGER_FILE.open("r", encoding="utf-8") as ledger_file:
        for line in ledger_file:
            if line.strip():
                records.append(json.loads(line))
    return records


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--format", required=True, choices=("csv", "json"))
    parser.add_argument("--out", required=True)
    parser.add_argument("--summary", action="store_true")
    return parser.parse_args()


def _write_json(records: list[dict], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(records, output_file, ensure_ascii=False)


def _write_csv(records: list[dict], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=CSV_FIELDS,
            lineterminator="\n",
        )
        writer.writeheader()
        for record in sorted(records, key=lambda item: item["id"]):
            payload = {
                key: value
                for key, value in record.items()
                if key not in RESERVED_FIELDS
            }
            writer.writerow(
                {
                    "id": record["id"],
                    "kind": record["kind"],
                    "tenant": record["tenant"],
                    "payload": json.dumps(
                        payload,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                }
            )


def main() -> int:
    args = _parse_args()

    if not LEDGER_FILE.exists():
        print(f"error: ledger not found: {LEDGER_FILE}", file=sys.stderr)
        return 2

    records = [
        record
        for record in _read_all()
        if record.get("tenant") == args.tenant
    ]

    output_path = Path(args.out)
    if args.format == "json":
        _write_json(records, output_path)
    else:
        _write_csv(records, output_path)

    if args.summary:
        counts = Counter(record["kind"] for record in records)
        for kind in sorted(counts):
            print(f"kind:{kind} count:{counts[kind]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
