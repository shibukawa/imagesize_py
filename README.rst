imagesize
=============

.. image:: https://travis-ci.org/shibukawa/imagesize_py.svg?branch=master
    :target: https://travis-ci.org/shibukawa/imagesize_py

This module analyzes jpeg/jpeg2000/png/gif image header and return image size.

.. code:: python

   import imagesize

   width, height = imagesize.get("test.png")
   print(width, height)

This module is pure python module.

API
-----

* ``imagesize.get(filepath)``

  Returns image size(width, height).

Benchmark
------------

It just parses only header, ignores pixel data. So it is much faster than Pillow.

.. list-table::
   :header-rows: 1

   - * module
     * result
   - * imagesize(pure python) 
     * 1.077 seconds per 100000 times
   - * Pillow
     * 10.569 seconds per 100000 times

I tested on MacBookPro(2014/Core i7) with 125kB PNG files.

License
-----------

MIT License

Thanks
----------

I refers the following codes:

* http://markasread.net/post/17551554979/get-image-size-info-using-pure-python-code
* http://stackoverflow.com/questions/8032642/how-to-obtain-image-size-using-standard-python-class-without-using-external-lib

Thank you for feedbacks:

* tk0miya (https://github.com/tk0miya)
* shimizukawa (https://github.com/shimizukawa)
* xantares (https://github.com/xantares)
* Ivan Zakharyaschev (https://github.com/imz)

