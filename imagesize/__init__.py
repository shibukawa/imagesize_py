import sys

__all__ = ("get",)

if sys.version_info[0] > 2:
    from .py3 import get
else:
    from py2 import get

