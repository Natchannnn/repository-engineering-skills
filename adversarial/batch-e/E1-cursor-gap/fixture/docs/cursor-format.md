# Cursor format (repo convention — normative for this fixture)

- A cursor carries the snapshot mark (max event id visible when the export
  started) and the scan position (last raw id scanned).
- The job keeps calling `scan()` until `next_cursor is None`, **including across
  empty pages**. An empty filtered page is not end-of-data.
- Records inserted after the snapshot mark are outside this export, even if they
  would pass the filter.
