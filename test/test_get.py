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

    def test_load_png_filelike(self):
        """ test_load_png_filelike
        """
        from io import BytesIO

        _ = os.path.join(imagedir, "test.png")
        with open(_, "rb") as fhandle:
            filelike = BytesIO(fhandle.read())

        width, height = imagesize.get(filelike)
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    def test_netpbm(self):
        for test_type in ["test", "test-ascii"]:
            for test_ext in ["pbm", "pgm", "ppm"]:
                test_file = os.path.join(imagedir, "{}.{}".format(test_type, test_ext))
                width, height = imagesize.get(test_file)
                self.assertEqual(width, 65)
                self.assertEqual(height, 20)

    def test_load_png_bytes(self):
        width, height = imagesize.get(os.path.join(imagedir_bytes, b"test.png"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    def test_load_jpeg_bytes(self):
        width, height = imagesize.get(os.path.join(imagedir_bytes, b"test.jpg"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    def test_load_jpeg2000_bytes(self):
        width, height = imagesize.get(os.path.join(imagedir_bytes, b"test.jp2"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    def test_load_gif_bytes(self):
        width, height = imagesize.get(os.path.join(imagedir_bytes, b"test.gif"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    def test_bigendian_tiff_bytes(self):
        width, height = imagesize.get(os.path.join(imagedir_bytes, b"test.tiff"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    def test_load_svg_bytes(self):
        width, height = imagesize.get(os.path.join(imagedir_bytes, b"test.svg"))
        self.assertEqual(width, 90)
        self.assertEqual(height, 60)

    def test_littleendian_tiff_bytes(self):
        width, height = imagesize.get(os.path.join(imagedir_bytes, b"multipage_tiff_example.tif"))
        self.assertEqual(width, 800)
        self.assertEqual(height, 600)

    @unittest.skipIf(Path is None, "requires pathlib support")
    def test_load_png_path(self):
        width, height = imagesize.get(Path(imagedir, "test.png"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    @unittest.skipIf(Path is None, "requires pathlib support")
    def test_load_jpeg_path(self):
        width, height = imagesize.get(Path(imagedir, "test.jpg"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    @unittest.skipIf(Path is None, "requires pathlib support")
    def test_load_jpeg2000_path(self):
        width, height = imagesize.get(Path(imagedir, "test.jp2"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    @unittest.skipIf(Path is None, "requires pathlib support")
    def test_load_gif_path(self):
        width, height = imagesize.get(Path(imagedir, "test.gif"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    @unittest.skipIf(Path is None, "requires pathlib support")
    def test_bigendian_tiff_path(self):
        width, height = imagesize.get(Path(imagedir, "test.tiff"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    @unittest.skipIf(Path is None, "requires pathlib support")
    def test_load_svg_path(self):
        width, height = imagesize.get(Path(imagedir, "test.svg"))
        self.assertEqual(width, 90)
        self.assertEqual(height, 60)

    @unittest.skipIf(Path is None, "requires pathlib support")
    def test_littleendian_tiff_path(self):
        width, height = imagesize.get(Path(imagedir, "multipage_tiff_example.tif"))
        self.assertEqual(width, 800)
        self.assertEqual(height, 600)
