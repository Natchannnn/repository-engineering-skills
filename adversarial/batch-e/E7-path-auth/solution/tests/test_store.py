import pathlib
import sys

sys.path.insert(0, pathlib.Path(__file__).parent.parent.as_posix())

from paths import DATA_FILE  # noqa: E402
from store import count  # noqa: E402


def test_data_file_is_path():
    assert isinstance(DATA_FILE, pathlib.PurePath)


def test_count(tmp_path):
    import paths

    old = paths.DATA_FILE
    paths.DATA_FILE = tmp_path / "r.jsonl"
    (tmp_path / "r.jsonl").write_text('{"a": 1}\n', encoding="utf-8")
    try:
        assert count() == 1
    finally:
        paths.DATA_FILE = old
