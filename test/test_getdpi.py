import unittest
import os
import imagesize

try:
    from pathlib import Path
except ImportError:
    # Python 2
    Path = None


imagedir = os.path.join(os.path.dirname(__file__), "images")
imagedir_bytes = imagedir.encode("utf-8")


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

    def test_png_bytes(self):
        xdpi, ydpi = imagesize.getDPI(os.path.join(imagedir_bytes, b"test.png"))
        self.assertEqual(xdpi, 72)
        self.assertEqual(ydpi, 72)

    def test_jpeg_bytes(self):
        xdpi, ydpi = imagesize.getDPI(os.path.join(imagedir_bytes, b"test.jpg"))
        self.assertEqual(xdpi, 72)
        self.assertEqual(ydpi, 72)

    def test_jpeg2000_bytes(self):
        xdpi, ydpi = imagesize.getDPI(os.path.join(imagedir_bytes, b"test.jp2"))
        self.assertEqual(xdpi, -1)
        self.assertEqual(ydpi, -1)

    def test_gif_bytes(self):
        xdpi, ydpi = imagesize.getDPI(os.path.join(imagedir_bytes, b"test.gif"))
        self.assertEqual(xdpi, -1)
        self.assertEqual(ydpi, -1)

    def test_bigendian_tiff_bytes(self):
        xdpi, ydpi = imagesize.getDPI(os.path.join(imagedir_bytes, b"test.tiff"))
        self.assertEqual(xdpi, -1)
        self.assertEqual(ydpi, -1)

    def test_svg_bytes(self):
        xdpi, ydpi = imagesize.getDPI(os.path.join(imagedir_bytes, b"test.svg"))
        self.assertEqual(xdpi, -1)
        self.assertEqual(ydpi, -1)

    def test_littleendian_tiff_bytes(self):
        xdpi, ydpi = imagesize.getDPI(os.path.join(imagedir_bytes, b"multipage_tiff_example.tif"))
        self.assertEqual(xdpi, -1)
        self.assertEqual(ydpi, -1)

    @unittest.skipIf(Path is None, "requires pathlib support")
    def test_png_path(self):
        xdpi, ydpi = imagesize.getDPI(Path(imagedir, "test.png"))
        self.assertEqual(xdpi, 72)
        self.assertEqual(ydpi, 72)

    @unittest.skipIf(Path is None, "requires pathlib support")
    def test_jpeg_path(self):
        xdpi, ydpi = imagesize.getDPI(Path(imagedir, "test.jpg"))
        self.assertEqual(xdpi, 72)
        self.assertEqual(ydpi, 72)

    @unittest.skipIf(Path is None, "requires pathlib support")
    def test_jpeg2000_path(self):
        xdpi, ydpi = imagesize.getDPI(Path(imagedir, "test.jp2"))
        self.assertEqual(xdpi, -1)
        self.assertEqual(ydpi, -1)

    @unittest.skipIf(Path is None, "requires pathlib support")
    def test_gif_path(self):
        xdpi, ydpi = imagesize.getDPI(Path(imagedir, "test.gif"))
        self.assertEqual(xdpi, -1)
        self.assertEqual(ydpi, -1)

    @unittest.skipIf(Path is None, "requires pathlib support")
    def test_bigendian_tiff_path(self):
        xdpi, ydpi = imagesize.getDPI(Path(imagedir, "test.tiff"))
        self.assertEqual(xdpi, -1)
        self.assertEqual(ydpi, -1)

    @unittest.skipIf(Path is None, "requires pathlib support")
    def test_svg_path(self):
        xdpi, ydpi = imagesize.getDPI(Path(imagedir, "test.svg"))
        self.assertEqual(xdpi, -1)
        self.assertEqual(ydpi, -1)

    @unittest.skipIf(Path is None, "requires pathlib support")
    def test_littleendian_tiff_path(self):
        xdpi, ydpi = imagesize.getDPI(Path(imagedir, "multipage_tiff_example.tif"))
        self.assertEqual(xdpi, -1)
        self.assertEqual(ydpi, -1)
