# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from radioplayer import version

data_files = []

readme = open('README.rst').read()

setup(name="radioplayer",
      version=version,
      description="A little radio player",
      long_description=readme,
      author="Philippe Normand",
      author_email='phil@base-art.net',
      license="GPL2",
      packages=find_packages(),
      include_package_data=True,
      data_files=data_files,
      url="http://base-art.net",
      download_url='http://base-art.net/static/radioplayer-%s.tar.gz' % version,
      keywords=['radio', 'multimedia', 'gstreamer', 'telepathy', 'd-bus',
                'libre.fm', 'last.fm'],
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Environment :: Console',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   ],
      entry_points="""\
      [console_scripts]
      radioplayer = radioplayer.main:main
      """,
)
