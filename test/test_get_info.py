import os
import unittest

import imagesize


imagedir = os.path.join(os.path.dirname(__file__), "images")
ROTATED_JPEG = os.path.join(imagedir, "test-rotated.jpg")
ROTATED_TIFF = os.path.join(imagedir, "test-rotated.tiff")


def test_get_info_defaults():
    info = imagesize.get_info(os.path.join(imagedir, "test.png"))
    assert info.width == 802
    assert info.height == 670
    assert info.xdpi == 72
    assert info.ydpi == 72
    assert info.colors == 16777216


def test_get_info_selective_fields():
    info = imagesize.get_info(os.path.join(imagedir, "test.png"), size=True, dpi=False, colors=False)
    assert info.width == 802
    assert info.height == 670
    assert info.xdpi == -1
    assert info.ydpi == -1
    assert info.colors == -1


def test_legacy_aliases():
    size = imagesize.get(os.path.join(imagedir, "test.jpg"))
    dpi = imagesize.getDPI(os.path.join(imagedir, "test.jpg"))
    assert size == (802, 670)
    assert dpi == (72, 72)


def test_get_info_applies_exif_rotation_by_default():
    info = imagesize.get_info(ROTATED_JPEG, dpi=False, colors=False)
    assert info.width == 20
    assert info.height == 40
    assert info.rotation == 6


def test_get_info_can_disable_exif_rotation():
    info = imagesize.get_info(ROTATED_JPEG, dpi=False, colors=False, exif_rotation=False)
    assert info.width == 40
    assert info.height == 20
    assert info.rotation == 6


def test_get_info_applies_tiff_rotation_by_default():
    info = imagesize.get_info(ROTATED_TIFF, dpi=False, colors=False)
    assert info.width == 20
    assert info.height == 40
    assert info.rotation == 6


def test_get_info_can_disable_tiff_rotation():
    info = imagesize.get_info(ROTATED_TIFF, dpi=False, colors=False, exif_rotation=False)
    assert info.width == 40
    assert info.height == 20
    assert info.rotation == 6
