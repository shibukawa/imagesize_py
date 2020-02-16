import unittest
import os
import imagesize

imagedir = os.path.join(os.path.dirname(__file__), "images")


class GetDPITest(unittest.TestCase):
    def test_png(self):
        xdpi, ydpi = imagesize.getDPI(os.path.join(imagedir, "test.png"))
        self.assertEqual(xdpi, 72)
        self.assertEqual(ydpi, 72)

    def test_jpeg(self):
        xdpi, ydpi = imagesize.getDPI(os.path.join(imagedir, "test.jpg"))
        self.assertEqual(xdpi, 72)
        self.assertEqual(ydpi, 72)

    def test_jpeg2000(self):
        xdpi, ydpi = imagesize.getDPI(os.path.join(imagedir, "test.jp2"))
        self.assertEqual(xdpi, -1)
        self.assertEqual(ydpi, -1)

    def test_gif(self):
        xdpi, ydpi = imagesize.getDPI(os.path.join(imagedir, "test.gif"))
        self.assertEqual(xdpi, -1)
        self.assertEqual(ydpi, -1)

    def test_bigendian_tiff(self):
        xdpi, ydpi = imagesize.getDPI(os.path.join(imagedir, "test.tiff"))
        self.assertEqual(xdpi, -1)
        self.assertEqual(ydpi, -1)

    def test_svg(self):
        xdpi, ydpi = imagesize.getDPI(os.path.join(imagedir, "test.svg"))
        self.assertEqual(xdpi, -1)
        self.assertEqual(ydpi, -1)

    def test_littleendian_tiff(self):
        xdpi, ydpi = imagesize.getDPI(os.path.join(imagedir, "multipage_tiff_example.tif"))
        self.assertEqual(xdpi, -1)
        self.assertEqual(ydpi, -1)
