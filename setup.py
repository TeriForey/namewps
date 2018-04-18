#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import os

from setuptools import setup, find_packages

version = __import__('testbird').__version__
here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

reqs = [line.strip() for line in open('requirements.txt')]

classifiers = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'Operating System :: MacOS :: MacOS X',
    'Operating System :: POSIX',
    'Programming Language :: Python',
    'Natural Language :: English',
    "Programming Language :: Python :: 2",
    'Programming Language :: Python :: 2.7',
    # 'Programming Language :: Python :: 3',
    # 'Programming Language :: Python :: 3.6',
    'Topic :: Scientific/Engineering :: Atmospheric Science',
    'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
]

setup(name='testbird',
      version='0.1.0',
      description="Testing how to build a bird",
      long_description=README + '\n\n' + CHANGES,
      author="Teri Forey",
      author_email='trf5@le.ac.uk',
      url='https://github.com/TeriForey/testbird',
      classifiers=classifiers,
      license="GNU General Public License v3",
      keywords='wps pywps birdhouse testbird',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='testbird',
      install_requires=reqs,
      entry_points={
          'console_scripts': [
             'testbird=testbird:main',
          ]},)
