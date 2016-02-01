import unittest
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import imagesize

imagedir = os.path.join(os.path.dirname(__file__), "images")

class GetByPurePythonTest(unittest.TestCase):
    def test_load_png(self):
        width, height = imagesize.get_by_purepython(os.path.join(imagedir, "test.png"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    def test_load_jpeg(self):
        width, height = imagesize.get_by_purepython(os.path.join(imagedir, "test.jpg"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    def test_load_gif(self):
        width, height = imagesize.get_by_purepython(os.path.join(imagedir, "test.gif"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

class GetByPILTest(unittest.TestCase):
    def test_load_png(self):
        width, height = imagesize.get_by_pil(os.path.join(imagedir, "test.png"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    def test_load_jpeg(self):
        width, height = imagesize.get_by_pil(os.path.join(imagedir, "test.jpg"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    def test_load_gif(self):
        width, height = imagesize.get_by_pil(os.path.join(imagedir, "test.gif"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

class GetTest(unittest.TestCase):
    def test_load_png(self):
        width, height = imagesize.get(os.path.join(imagedir, "test.png"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    def test_load_jpeg(self):
        width, height = imagesize.get(os.path.join(imagedir, "test.jpg"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    def test_load_gif(self):
        width, height = imagesize.get(os.path.join(imagedir, "test.gif"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)
