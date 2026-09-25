import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

LEDGER_FILE = "ledger.jsonl"
_MODULE_DIR = Path(__file__).resolve().parent


def _ledger_path() -> Path:
    return _MODULE_DIR / LEDGER_FILE


def _read_records() -> list[dict]:
    with _ledger_path().open("r", encoding="utf-8") as ledger_file:
        return [json.loads(line) for line in ledger_file if line.strip()]


def _payload(record: dict) -> str:
    payload = {
        key: value
        for key, value in record.items()
        if key not in {"id", "kind", "tenant"}
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _write_csv(records: list[dict], output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8", newline="") as output_file:
        writer = csv.writer(output_file, lineterminator="\n")
        writer.writerow(["id", "kind", "tenant", "payload"])
        for record in sorted(records, key=lambda item: item["id"]):
            writer.writerow(
                [record["id"], record["kind"], record["tenant"], _payload(record)]
            )


def _write_json(records: list[dict], output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(records, output_file, ensure_ascii=False)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--format", required=True, choices=("csv", "json"))
    parser.add_argument("--out", required=True)
    parser.add_argument("--summary", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    try:
        records = _read_records()
    except FileNotFoundError:
        print(f"{LEDGER_FILE} not found", file=sys.stderr)
        return 2

    filtered = [record for record in records if record.get("tenant") == args.tenant]

    if args.format == "csv":
        _write_csv(filtered, args.out)
    else:
        _write_json(filtered, args.out)

    if args.summary:
        counts = Counter(record["kind"] for record in filtered)
        for kind in sorted(counts):
            print(f"kind:{kind} count:{counts[kind]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
