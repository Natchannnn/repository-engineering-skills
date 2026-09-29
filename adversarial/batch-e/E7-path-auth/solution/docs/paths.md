# Paths

`DATA_FILE` is a `pathlib.Path` pointing at the JSONL records file (migrated from
`str`; callers pass it straight to `open`, which accepts both). `CACHE_DIR` is the
scratch directory name and stays a plain string.
