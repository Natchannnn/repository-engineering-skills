import argparse
import csv
import json
import sys
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

LEDGER_FILE = "ledger.jsonl"
CSV_HEADER = ["id", "kind", "tenant", "payload"]


def _ledger_path() -> Path:
    return Path(__file__).resolve().parent / LEDGER_FILE


def _read_records(path: Path) -> list[dict]:
    records = []
    for line in path.read_bytes().splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _payload(record: dict) -> str:
    payload = {
        key: value
        for key, value in record.items()
        if key not in {"id", "kind", "tenant"}
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _write_csv(records: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(CSV_HEADER)
        for record in sorted(records, key=lambda item: item["id"]):
            writer.writerow(
                [
                    record["id"],
                    record["kind"],
                    record["tenant"],
                    _payload(record),
                ]
            )


def _write_json(records: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8") as stream:
        json.dump(records, stream, separators=(",", ":"))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export ledger records for one tenant.")
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--format", choices=("csv", "json"), required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--summary", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    ledger_path = _ledger_path()
    if not ledger_path.is_file():
        print(f"{LEDGER_FILE} not found: {ledger_path}", file=sys.stderr)
        return 2

    records = _read_records(ledger_path)
    filtered = [record for record in records if record.get("tenant") == args.tenant]
    output_path = Path(args.out)

    if args.format == "csv":
        _write_csv(filtered, output_path)
    else:
        _write_json(filtered, output_path)

    if args.summary:
        counts = Counter(record["kind"] for record in filtered)
        for kind in sorted(counts):
            print(f"kind:{kind} count:{counts[kind]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
