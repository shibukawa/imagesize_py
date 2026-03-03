import os
import unittest

import imagesize


imagedir = os.path.join(os.path.dirname(__file__), "images")


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
        info = imagesize.get_info(os.path.join(imagedir, "test.png"), size=True, dpi=False, colors=False, channels=False)
        self.assertEqual(info.width, 802)
        self.assertEqual(info.height, 670)
        self.assertEqual(info.xdpi, -1)
        self.assertEqual(info.ydpi, -1)
        self.assertEqual(info.colors, -1)
        self.assertEqual(info.channels, -1)

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
