import unittest
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import imagesize

imagedir = os.path.join(os.path.dirname(__file__), "images")


class GetTest(unittest.TestCase):
    def test_load_png(self):
        width, height = imagesize.get(os.path.join(imagedir, "test.png"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    def test_load_jpeg(self):
        width, height = imagesize.get(os.path.join(imagedir, "test.jpg"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    def test_load_jpeg2000(self):
        width, height = imagesize.get(os.path.join(imagedir, "test.jp2"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    def test_load_gif(self):
        width, height = imagesize.get(os.path.join(imagedir, "test.gif"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    def test_bigendian_tiff(self):
        width, height = imagesize.get(os.path.join(imagedir, "test.tiff"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    def test_load_svg(self):
        width, height = imagesize.get(os.path.join(imagedir, "test.svg"))
        self.assertEqual(width, 90)
        self.assertEqual(height, 60)

    def test_littleendian_tiff(self):
        width, height = imagesize.get(os.path.join(imagedir, "multipage_tiff_example.tif"))
        self.assertEqual(width, 800)
        self.assertEqual(height, 600)
