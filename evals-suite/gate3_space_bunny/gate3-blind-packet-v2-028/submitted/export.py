"""CLI export of one tenant's records from the append-only JSON-lines ledger.

CP4 slice: filter by tenant and write CSV or JSON, with an optional per-kind
summary on stdout. The ledger path is resolved relative to this module so
callers are unaffected by the working directory.

Filtering reuses query.find() so an export selects exactly what a query would:
exact, case-sensitive tenant match in ledger file order. Only the CSV column
order differs from file order, because a row is sorted by ledger ID.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import Counter

import query

# The existence check below needs the ledger path, and query.LEDGER_PATH is the
# same "next to the module" location query actually reads, so it is aliased
# rather than recomputed: a separate formula could drift and check a file
# nobody reads.
LEDGER_PATH = query.LEDGER_PATH

# Promoted to CSV columns instead of being repeated inside the payload.
LEDGER_FIELDS = ("id", "kind", "tenant")

CSV_HEADER = ("id", "kind", "tenant", "payload")


def _payload(record: dict) -> str:
    """Return the record minus the ledger's own fields, as compact sorted JSON.

    Key order comes from sort_keys so two ledgers holding the same event fields
    in different insertion order export identical payloads.
    """
    rest = {key: value for key, value in record.items() if key not in LEDGER_FIELDS}
    return json.dumps(rest, sort_keys=True, separators=(",", ":"))


def _id_order(record: dict) -> tuple:
    """Return a sort key ordering records by ascending ledger ID.

    ledger.append lets an event supply its own "id" (the record is built as
    {"id": event_id, **event}), so a non-integer ID is representable. Integers
    sort first and numerically; anything else falls back to its text form, which
    keeps the ordering total instead of raising on a mix of int and str.
    """
    value = record.get("id")
    if isinstance(value, bool) or not isinstance(value, int):
        return (1, 0, str(value))
    return (0, value, "")


def _write_csv(records: list[dict], out_path: str) -> None:
    """Write the header plus one row per record, ordered by ascending ID.

    newline="" hands line-ending control to the writer; without it a Windows
    text stream would add a second newline on top of the one requested here.
    """
    with open(out_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(CSV_HEADER)
        for record in sorted(records, key=_id_order):
            writer.writerow(
                [record.get("id"), record.get("kind"), record.get("tenant"), _payload(record)]
            )


def _write_json(records: list[dict], out_path: str) -> None:
    """Write the records verbatim as a JSON array, in ledger file order."""
    with open(out_path, "w", encoding="utf-8", newline="") as handle:
        handle.write(json.dumps(records))
        handle.write("\n")


def _print_summary(records: list[dict]) -> None:
    """Print one 'kind:<k> count:<n>' line per kind present, ordered by kind."""
    counts = Counter(record.get("kind") for record in records)
    for kind in sorted(counts):
        print(f"kind:{kind} count:{counts[kind]}")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export one tenant's ledger records to CSV or JSON."
    )
    parser.add_argument(
        "--tenant", required=True, help="tenant to export; matched exactly"
    )
    parser.add_argument(
        "--format", required=True, choices=("csv", "json"), help="output format"
    )
    parser.add_argument("--out", required=True, help="path of the file to write")
    parser.add_argument(
        "--summary", action="store_true", help="also print per-kind counts to stdout"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run one export and return its process exit code."""
    args = _parse_args(argv)

    # An absent ledger is an error rather than an empty result: silently
    # exporting a header-only CSV would hide a wrong working setup behind a
    # plausible-looking empty report. Checked before opening --out so a failed
    # run leaves no output file behind.
    if not os.path.exists(LEDGER_PATH):
        print(f"error: ledger not found: {LEDGER_PATH}", file=sys.stderr)
        return 2

    records = query.find(tenant=args.tenant)

    if args.format == "csv":
        _write_csv(records, args.out)
    else:
        _write_json(records, args.out)

    # After the file write, so a successful run's report always matches what
    # landed on disk. An empty result prints nothing and still exits 0.
    if args.summary:
        _print_summary(records)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
