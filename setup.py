#!/usr/bin/env python

from setuptools import setup
#from distutils.core import setup

setup(name='imagesize',
      version='0.7.1',
      description='Getting image size from png/jpeg/jpeg2000/gif file',
      long_description='''
It parses image files' header and return image size.

* PNG
* JPEG
* JPEG2000
* GIF

This is a pure Python library.
''',
      author='Yoshiki Shibukawa',
      author_email='yoshiki at shibu.jp',
      url='https://github.com/shibukawa/imagesize_py',
      license="MIT",
      packages=['imagesize'],
      package_dir={"imagesize": "imagesize"},
      classifiers = [
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: Implementation :: PyPy',
          'Topic :: Multimedia :: Graphics'
     ]
)
