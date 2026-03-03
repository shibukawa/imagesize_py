#!/usr/bin/env python

from setuptools import setup
from imagesize import __version__

setup(name='imagesize',
      version=__version__,
      description='Getting image size from png/jpeg/jpeg2000/gif file',
      long_description='''
It parses image files' header and return image size.

* BMP
* PNG
* JPEG
* JPEG2000
* GIF
* TIFF
* SVG
* Netpbm
* WebP

This is a pure Python library.
''',
      author='Yoshiki Shibukawa',
      author_email='yoshiki@shibu.jp',
      url='https://github.com/shibukawa/imagesize_py',
      license="MIT",
      packages=['imagesize'],
      python_requires=">=3.10,<3.15",

      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3 :: Only',
          'Programming Language :: Python :: 3.10',
          'Programming Language :: Python :: 3.11',
          'Programming Language :: Python :: 3.12',
          'Programming Language :: Python :: 3.13',
          'Programming Language :: Python :: 3.14',
          'Programming Language :: Python :: Implementation :: CPython',
          'Programming Language :: Python :: Implementation :: PyPy',
          'Topic :: Multimedia :: Graphics'
     ]
)
