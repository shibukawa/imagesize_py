import sys

__all__ = ("get", "get_by_pil", "get_by_purepython")

if sys.version_info[0] > 2:
    from .py3 import get_by_purepython, get_by_pil
else:
    from py2 import get_by_purepython, get_by_pil

def get(filepath):
    width, height = get_by_purepython(filepath)
    if width == -1 or height == -1:
        return get_by_pil(filepath)
    return width, height

