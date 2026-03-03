imagesize
=============

.. image:: https://github.com/shibukawa/imagesize_py/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/shibukawa/imagesize_py/actions/workflows/ci.yml

.. image:: https://img.shields.io/pypi/v/imagesize.svg
    :target: https://pypi.org/project/imagesize/
    :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/imagesize.svg
    :target: https://pypi.org/project/imagesize/
    :alt: Supported Python versions

.. image:: https://img.shields.io/pypi/l/imagesize.svg
    :target: https://github.com/shibukawa/imagesize_py/blob/main/LICENSE.rst
    :alt: License

This module analyzes JPEG/JPEG 2000/PNG/GIF/TIFF/SVG/Netpbm/WebP/AVIF image headers and returns image size, DPI, and related metadata.

.. code:: python

   import imagesize

   width, height = imagesize.get("test.png")
   print(width, height)

   xdpi, ydpi = imagesize.getDPI("test.png")
   print(xdpi, ydpi)

   info = imagesize.get_info("test.png")
   print(info.width, info.height, info.rotation, info.xdpi, info.ydpi, info.colors, info.channels)

This module is a pure Python module. You can use file like object like file or something like ``io.BytesIO``.

Supported Python versions: 3.10-3.14

API
-----

* ``imagesize.get(filepath: FileInput, *, exif_rotation: bool = True) -> tuple[int, int]``

  Returns image size as ``(width, height)``. By default, orientation metadata is applied for rotated JPEG/TIFF images; pass ``exif_rotation=False`` to get the stored size as-is.

* ``imagesize.getDPI(filepath: FileInput) -> tuple[int, int]``

  Returns image DPI as ``(xdpi, ydpi)``.

* ``imagesize.get_info(filepath: FileInput, *, size: bool = True, dpi: bool = True, colors: bool = True, exif_rotation: bool = True, channels: bool = True) -> ImageInfo``

  Returns an ``ImageInfo`` named tuple with ``width``, ``height``, ``rotation``, ``xdpi``, ``ydpi``, ``colors`` and ``channels`` fields. ``rotation`` contains orientation metadata (e.g. EXIF Orientation tag, or ``-1`` when unavailable).

Benchmark
------------

It only parses headers, and ignores pixel data. So it is much faster than Pillow.

.. list-table::
   :header-rows: 1

   - * module
     * result
   - * imagesize (pure Python)
     * 1.077 seconds per 100 000 times
   - * Pillow
     * 10.569 seconds per 100 000 times

I tested on MacBookPro (2014/Core i7) with 125kB PNG files.

Development
---------------

Run test with the following command:

.. code:: bash

   python -m unittest

License
-----------

MIT License

* test/images/test.heic: https://nokiatech.github.io/heif/examples.html
* test/images/test.avif: https://libre-software.net/image/avif-test/

Thanks
----------

I referred to the following code:

* http://markasread.net/post/17551554979/get-image-size-info-using-pure-python-code
* https://stackoverflow.com/questions/8032642/how-to-obtain-image-size-using-standard-python-class-without-using-external-lib

I use sample image from here:

* https://www.nightprogrammer.org/development/multipage-tiff-example-download-test-image-file/

Thank you for feedback:

* tk0miya (https://github.com/tk0miya)
* shimizukawa (https://github.com/shimizukawa)
* xantares (https://github.com/xantares)
* Ivan Zakharyaschev (https://github.com/imz)
* Jon Dufresne (https://github.com/jdufresne)
* Geoff Lankow (https://github.com/darktrojan)
* Hugo (https://github.com/hugovk)
* Jack Cherng (https://github.com/jfcherng)
* Tyler A. Young (https://github.com/s3cur3)
* Mark Browning (https://github.com/mabrowning)
* ossdev07 (https://github.com/ossdev07)
* Nicholas-Schaub (https://github.com/Nicholas-Schaub)
* Nuffknacker (https://github.com/Nuffknacker) 
* Hannes Römer (https://github.com/hroemer)
* mikey (https://github.com/ffreemt)
* Marco (https://github.com/marcoffee)
* ExtReMLapin (https://github.com/ExtReMLapin)
* gremur (https://github.com/gremur)
* fuyb1992 (https://github.com/fuyb1992)
* flagman (https://github.com/flagman)
