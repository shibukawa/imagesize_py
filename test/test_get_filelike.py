"""
Tests imagesize.get for file-like objects.
"""

import os
import sys
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import imagesize


class _WrappedFileLike:
    """Minimal read/seek wrapper to validate duck-typed file-like support."""

    def __init__(self, raw: bytes):
        self._buffer = BytesIO(raw)

    def read(self, size: int = -1) -> bytes:
        return self._buffer.read(size)

    def seek(self, offset: int, whence: int = 0) -> int:
        return self._buffer.seek(offset, whence)


imagedir = os.path.join(os.path.dirname(__file__), "images")


def test_get_filelike():
    """test_get_filelike."""

    with open(os.path.join(imagedir, "test.jpg"), "rb") as fhandle:
        raw = fhandle.read()

    file_like = BytesIO(raw)

    assert imagesize.get(file_like) == (802, 670)


def test_get_file_object():
    """Accept standard file objects as file-like input."""

    with open(os.path.join(imagedir, "test.png"), "rb") as fhandle:
        assert imagesize.get(fhandle) == (802, 670)


def test_get_wrapped_filelike():
    """Accept non-IOBase objects implementing read/seek."""

    with open(os.path.join(imagedir, "test.jpg"), "rb") as fhandle:
        file_like = _WrappedFileLike(fhandle.read())

    assert imagesize.get(file_like) == (802, 670)
