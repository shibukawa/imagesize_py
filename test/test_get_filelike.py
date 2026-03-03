"""
test imagesize.get for filelike object io.BytesIO(raw bytes)

to test:
pytest -k test_get_filelike
"""

import os
import sys

from io import BytesIO
from urllib.request import urlopen

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import imagesize


def test_get_filelike():
    """ test_get_filelike. """

    url = 'https://www.tsln.com/wp-content/uploads/2018/10/bears-tsln-101318-3-1240x826.jpg'
    try:
        response = urlopen(url)
        raw = response.read()
    except Exception as exc:
        raise SystemExit(exc)

    file_like = BytesIO(raw)

    assert imagesize.get(file_like) == (1240, 826)
