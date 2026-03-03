import os
import unittest
from pathlib import Path

import imagesize

imagedir = os.path.join(os.path.dirname(__file__), "images")
imagedir_bytes = imagedir.encode("utf-8")
bmpfile = os.path.join(imagedir, "test_24.bmp")
bmpfile_bytes = os.path.join(imagedir_bytes, b"test_24.bmp")
ROTATED_JPEG = os.path.join(imagedir, "test-rotated.jpg")
ROTATED_TIFF = os.path.join(imagedir, "test-rotated.tiff")


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

    def test_load_bmp(self):
        width, height = imagesize.get(bmpfile)
        self.assertEqual(width, 100)
        self.assertEqual(abs(height), 300)

    def test_bigendian_tiff(self):
        width, height = imagesize.get(os.path.join(imagedir, "test.tiff"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    def test_load_svg(self):
        width, height = imagesize.get(os.path.join(imagedir, "test.svg"))
        self.assertEqual(width, 90)
        self.assertEqual(height, 60)

    def test_load_svg_float_length(self):
        from io import BytesIO

        filelike = BytesIO(b'<svg width="25.4mm" height="12.7mm" xmlns="http://www.w3.org/2000/svg"></svg>')
        width, height = imagesize.get(filelike)
        self.assertEqual(width, 96)
        self.assertEqual(height, 48)

    def test_littleendian_tiff(self):
        width, height = imagesize.get(os.path.join(imagedir, "multipage_tiff_example.tif"))
        self.assertEqual(width, 800)
        self.assertEqual(height, 600)

    def test_load_svg_pt(self):
        from io import BytesIO

        svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="72pt" height="36pt"></svg>'
        width, height = imagesize.get(BytesIO(svg))
        self.assertEqual(width, 96)
        self.assertEqual(height, 48)

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

    def test_load_bmp_bytes(self):
        width, height = imagesize.get(bmpfile_bytes)
        self.assertEqual(width, 100)
        self.assertEqual(abs(height), 300)

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

    def test_load_avif(self):
        width, height = imagesize.get(os.path.join(imagedir, "test.avif"))
        self.assertEqual(width, 630)
        self.assertEqual(height, 420)

    def test_load_avif_bytes(self):
        width, height = imagesize.get(os.path.join(imagedir_bytes, b"test.avif"))
        self.assertEqual(width, 630)
        self.assertEqual(height, 420)

    def test_load_webp_vp8x(self):
        """Test VP8X format WebP file parsing.
        
        VP8X format stores dimensions as (width-1, height-1) in the header,
        so the parser must add 1 to get the actual dimensions.
        """
        width, height = imagesize.get(os.path.join(imagedir, "test_vp8x.webp"))
        self.assertEqual(width, 200)
        self.assertEqual(height, 1)

    def test_load_png_path(self):
        width, height = imagesize.get(Path(imagedir, "test.png"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    def test_load_jpeg_path(self):
        width, height = imagesize.get(Path(imagedir, "test.jpg"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    def test_load_jpeg2000_path(self):
        width, height = imagesize.get(Path(imagedir, "test.jp2"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    def test_load_gif_path(self):
        width, height = imagesize.get(Path(imagedir, "test.gif"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    def test_load_bmp_path(self):
        width, height = imagesize.get(Path(bmpfile))
        self.assertEqual(width, 100)
        self.assertEqual(abs(height), 300)

    def test_bigendian_tiff_path(self):
        width, height = imagesize.get(Path(imagedir, "test.tiff"))
        self.assertEqual(width, 802)
        self.assertEqual(height, 670)

    def test_load_svg_path(self):
        width, height = imagesize.get(Path(imagedir, "test.svg"))
        self.assertEqual(width, 90)
        self.assertEqual(height, 60)

    def test_littleendian_tiff_path(self):
        width, height = imagesize.get(Path(imagedir, "multipage_tiff_example.tif"))
        self.assertEqual(width, 800)
        self.assertEqual(height, 600)

    def test_load_jpeg_with_exif_rotation_default(self):
        width, height = imagesize.get(ROTATED_JPEG)
        self.assertEqual(width, 20)
        self.assertEqual(height, 40)

    def test_load_jpeg_with_exif_rotation_disabled(self):
        width, height = imagesize.get(ROTATED_JPEG, exif_rotation=False)
        self.assertEqual(width, 40)
        self.assertEqual(height, 20)


    def test_load_tiff_with_exif_rotation_default(self):
        width, height = imagesize.get(ROTATED_TIFF)
        self.assertEqual(width, 20)
        self.assertEqual(height, 40)

    def test_load_tiff_with_exif_rotation_disabled(self):
        width, height = imagesize.get(ROTATED_TIFF, exif_rotation=False)
        self.assertEqual(width, 40)
        self.assertEqual(height, 20)
