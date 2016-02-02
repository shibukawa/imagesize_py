import unittest
import os, sys
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
