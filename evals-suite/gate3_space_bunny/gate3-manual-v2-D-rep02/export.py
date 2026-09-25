import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

LEDGER_FILE = "ledger.jsonl"
RESERVED_FIELDS = {"id", "kind", "tenant"}


def _ledger_path() -> Path:
    return Path(__file__).resolve().parent / LEDGER_FILE


def _read_records() -> list[dict] | None:
    try:
        contents = _ledger_path().read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"error: {LEDGER_FILE} not found", file=sys.stderr)
        return None

    records = []
    for line in contents.splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _write_csv(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(["id", "kind", "tenant", "payload"])
        for record in sorted(records, key=lambda item: item["id"]):
            payload = {
                key: value
                for key, value in record.items()
                if key not in RESERVED_FIELDS
            }
            encoded_payload = json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            writer.writerow(
                [record["id"], record["kind"], record["tenant"], encoded_payload]
            )


def _write_json(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as output:
        output.write(json.dumps(records, ensure_ascii=False, separators=(",", ":")))


def _print_summary(records: list[dict]) -> None:
    counts = Counter(record["kind"] for record in records)
    for kind in sorted(counts):
        print(f"kind:{kind} count:{counts[kind]}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--format", required=True, choices=["csv", "json"])
    parser.add_argument("--out", required=True)
    parser.add_argument("--summary", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    records = _read_records()
    if records is None:
        return 2

    filtered_records = [
        record for record in records if record.get("tenant") == args.tenant
    ]
    output_path = Path(args.out)
    try:
        if args.format == "csv":
            _write_csv(output_path, filtered_records)
        else:
            _write_json(output_path, filtered_records)
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if args.summary:
        _print_summary(filtered_records)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
