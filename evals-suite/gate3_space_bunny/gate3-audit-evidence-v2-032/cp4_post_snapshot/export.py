"""Export one tenant's ledger records to CSV or JSON.

Records are read from the same ``ledger.jsonl`` that :mod:`ledger` writes, next
to this module, and the tenant filter is delegated to :func:`query.find` so an
export obeys exactly the contract the query side already offers: exact,
case-sensitive equality, and file order.

The two formats differ deliberately in ordering. CSV is row-per-record sorted by
ascending ``id``; the JSON document keeps file order. A tenant with no records is
not an error -- the CSV is header-only and the JSON document is ``[]`` -- but a
missing ledger is, because "no ledger" and "empty ledger" mean different things
here. Exit codes are 0 on success, 1 when the destination cannot be written, and
2 when the ledger is missing or unreadable, or when the command line is rejected.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from typing import Any, NoReturn, Sequence

from query import LEDGER_PATH, find

CSV_COLUMNS = ("id", "kind", "tenant", "payload")
RESERVED_COLUMNS = frozenset({"id", "kind", "tenant"})
STDOUT_TARGET = "-"
EXIT_OK = 0
EXIT_WRITE_ERROR = 1
EXIT_LEDGER_ERROR = 2


def _fail(message: str, code: int) -> NoReturn:
    """Report ``message`` on stderr and abort with ``code``."""
    print(f"export.py: {message}", file=sys.stderr)
    raise SystemExit(code)


def _require_ledger() -> None:
    """Abort with :data:`EXIT_LEDGER_ERROR` unless the ledger exists and is readable.

    :func:`query.find` deliberately reads a missing ledger as an empty one, so
    this probe is what lets the CLI tell those two cases apart.
    """
    try:
        with LEDGER_PATH.open("rb") as handle:
            handle.read(1)
    except FileNotFoundError:
        _fail(f"ledger file not found: {LEDGER_PATH}", EXIT_LEDGER_ERROR)
    except OSError as exc:
        _fail(f"cannot read ledger {LEDGER_PATH}: {exc}", EXIT_LEDGER_ERROR)


def _cell(value: Any) -> str:
    """Render one CSV field: an absent value becomes an empty cell, not ``None``."""
    return "" if value is None else str(value)


def _id_order(record: dict) -> tuple[int, int, str]:
    """Sort key ordering records by ascending numeric ``id``.

    Ids written by :func:`ledger.append` are integers, so the normal case is a
    plain numeric sort. A hand-edited or legacy record whose ``id`` is missing or
    not an integer still lands in a deterministic place -- after the numeric ids,
    compared as text -- instead of making the sort raise.
    """
    value = record.get("id")
    if isinstance(value, int) and not isinstance(value, bool):
        return (0, value, "")
    return (1, 0, _cell(value))


def _payload(record: dict) -> str:
    """Render ``record`` minus the id/kind/tenant columns as a compact JSON object.

    Keys are sorted and the separators drop every space, so one record always
    renders to the same payload text.
    """
    rest = {key: value for key, value in record.items() if key not in RESERVED_COLUMNS}
    return json.dumps(rest, sort_keys=True, separators=(",", ":"))


def _render_csv(records: list[dict]) -> str:
    """Render the CSV document: header, then one row per record by ascending id."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(CSV_COLUMNS)
    for record in sorted(records, key=_id_order):
        writer.writerow(
            [
                _cell(record.get("id")),
                _cell(record.get("kind")),
                _cell(record.get("tenant")),
                _payload(record),
            ]
        )
    return buffer.getvalue()


def _render_json(records: list[dict]) -> str:
    """Render the JSON document: the filtered records, in file order."""
    return json.dumps(records, ensure_ascii=False, indent=2) + "\n"


def _summary_lines(records: list[dict]) -> list[str]:
    """Return one ``kind:<k> count:<n>`` line per kind in ``records``, sorted by kind.

    Kinds are grouped by their text form, so a ledger holding a non-string kind
    still yields a total, sorted summary rather than an unhashable-key crash.
    """
    counts: dict[str, int] = {}
    for record in records:
        label = _cell(record.get("kind"))
        counts[label] = counts.get(label, 0) + 1
    return [f"kind:{label} count:{count}" for label, count in sorted(counts.items())]


def _write(document: str, target: str) -> None:
    """Write ``document`` to ``target``, or to stdout when ``target`` is ``-``.

    Newline translation is disabled so the ``\\n`` terminators the renderers emit
    reach the file unchanged on every platform.
    """
    if target == STDOUT_TARGET:
        sys.stdout.write(document)
        return
    try:
        with open(target, "w", encoding="utf-8", newline="") as handle:
            handle.write(document)
    except OSError as exc:
        _fail(f"cannot write {target}: {exc}", EXIT_WRITE_ERROR)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="export.py",
        description="Export the ledger records of a single tenant to CSV or JSON.",
    )
    parser.add_argument(
        "--tenant",
        required=True,
        help="tenant to export; matched exactly and case-sensitively",
    )
    parser.add_argument(
        "--format",
        choices=("csv", "json"),
        default="csv",
        help="document format to write (default: csv)",
    )
    parser.add_argument(
        "--out",
        default=STDOUT_TARGET,
        metavar="PATH",
        help=f"destination file, or {STDOUT_TARGET!r} for stdout (default: {STDOUT_TARGET})",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="also print a 'kind:<k> count:<n>' line per kind, sorted by kind, to stdout",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the export CLI and return the process exit code."""
    args = _build_parser().parse_args(argv)

    _require_ledger()
    records = find(tenant=args.tenant)

    if args.format == "json":
        document = _render_json(records)
    else:
        document = _render_csv(records)
    _write(document, args.out)

    if args.summary:
        for line in _summary_lines(records):
            print(line)
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
