import os
import unittest

import imagesize


imagedir = os.path.join(os.path.dirname(__file__), "images")
ROTATED_HEIC = os.path.join(imagedir, "test_rotated.heic")
if not os.path.exists(ROTATED_HEIC):
    ROTATED_HEIC = os.path.join(imagedir, "test-rotated.heic")
ROTATED_AVIF = os.path.join(imagedir, "test-rotated.avif")


class GetInfoTest(unittest.TestCase):
    def test_get_info_defaults(self):
        info = imagesize.get_info(os.path.join(imagedir, "test.png"))
        self.assertEqual(info.width, 802)
        self.assertEqual(info.height, 670)
        self.assertEqual(info.xdpi, 72)
        self.assertEqual(info.ydpi, 72)
        self.assertEqual(info.colors, 16777216)
        self.assertEqual(info.channels, 4)

    def test_get_info_selective_fields(self):
        info = imagesize.get_info(os.path.join(imagedir, "test.png"), size=True, dpi=False, colors=False, channels=False, exif_rotation=False)
        self.assertEqual(info.width, 802)
        self.assertEqual(info.height, 670)
        self.assertEqual(info.xdpi, -1)
        self.assertEqual(info.ydpi, -1)
        self.assertEqual(info.colors, -1)
        self.assertEqual(info.channels, -1)
        self.assertEqual(info.rotation, -1)

    def test_legacy_aliases(self):
        size = imagesize.get(os.path.join(imagedir, "test.jpg"))
        dpi = imagesize.getDPI(os.path.join(imagedir, "test.jpg"))
        self.assertEqual(size, (802, 670))
        self.assertEqual(dpi, (72, 72))

    def test_get_info_invalid_input(self):
        with self.assertRaises(FileNotFoundError):
            imagesize.get_info(os.path.join(imagedir, "missing-file.png"))

    def test_get_info_channels_jpeg(self):
        info = imagesize.get_info(os.path.join(imagedir, "test.jpg"))
        self.assertEqual(info.channels, 3)
            
    def test_shortcuts_invalid_input(self):
        missing = os.path.join(imagedir, "missing-file.png")
        self.assertEqual(imagesize.get(missing), (-1, -1))
        self.assertEqual(imagesize.getDPI(missing), (-1, -1))
    
    def test_get_info_applies_exif_rotation_by_default(self):
        info = imagesize.get_info(os.path.join(imagedir, "test-rotated.jpg"), dpi=False, colors=False)
        self.assertEqual(info.width, 670)
        self.assertEqual(info.height, 802)
        self.assertEqual(info.rotation, 6)


    def test_get_info_can_disable_exif_rotation(self):
        info = imagesize.get_info(os.path.join(imagedir, "test-rotated.jpg"), dpi=False, colors=False, exif_rotation=False)
        self.assertEqual(info.width, 802)
        self.assertEqual(info.height, 670)
        self.assertEqual(info.rotation, 6)


    def test_get_info_applies_tiff_rotation_by_default(self):
        info = imagesize.get_info(os.path.join(imagedir, "test-rotated.tiff"), dpi=False, colors=False)
        self.assertEqual(info.width, 670)
        self.assertEqual(info.height, 802)
        self.assertEqual(info.rotation, 6)


    def test_get_info_can_disable_tiff_rotation(self):
        info = imagesize.get_info(os.path.join(imagedir, "test-rotated.tiff"), dpi=False, colors=False, exif_rotation=False)
        self.assertEqual(info.width, 802)
        self.assertEqual(info.height, 670)
        self.assertEqual(info.rotation, 6)

    def test_get_info_applies_heic_rotation_by_default(self):
        info = imagesize.get_info(ROTATED_HEIC, dpi=False, colors=False)
        raw = imagesize.get_info(ROTATED_HEIC, dpi=False, colors=False, exif_rotation=False)
        expected = (raw.height, raw.width) if raw.rotation in {5, 6, 7, 8} else (raw.width, raw.height)
        self.assertEqual((info.width, info.height), expected)
        self.assertEqual(info.rotation, raw.rotation)

    def test_get_info_can_disable_heic_rotation(self):
        info = imagesize.get_info(ROTATED_HEIC, dpi=False, colors=False, exif_rotation=False)
        self.assertEqual(info.width, 1440)
        self.assertEqual(info.height, 960)

    def test_get_info_applies_avif_rotation_by_default(self):
        info = imagesize.get_info(ROTATED_AVIF, dpi=False, colors=False)
        self.assertEqual(info.width, 420)
        self.assertEqual(info.height, 630)
        self.assertEqual(info.rotation, 6)

    def test_get_info_can_disable_avif_rotation(self):
        info = imagesize.get_info(ROTATED_AVIF, dpi=False, colors=False, exif_rotation=False)
        self.assertEqual(info.width, 630)
        self.assertEqual(info.height, 420)
        self.assertEqual(info.rotation, 6)
