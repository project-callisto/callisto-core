#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import sys
import pypandoc

from callisto_core import __version__ as version

from setuptools import setup, find_packages

if sys.argv[-1] == 'publish':
    try:
        import wheel
        print("Wheel version: ", wheel.__version__)
    except ImportError:
        print('Wheel library missing. Please run "pip install wheel"')
        sys.exit()
    os.system('python setup.py sdist upload')
    os.system('python setup.py bdist_wheel upload')
    sys.exit()

if sys.argv[-1] == 'tag':
    print("Tagging the version on github:")
    os.system("git tag -a %s -m 'version %s'" % (version, version))
    os.system("git push --tags")
    sys.exit()

try:
    long_description = pypandoc.convert_file('README.md', 'rst') + \
        pypandoc.convert_file('docs/HISTORY.md', 'rst')
except BaseException:
    long_description = ''

license = open('LICENSE').read()

setup(
    name='callisto-core',
    version=version,
    description='Report intake, escrow, matching and secure delivery code for Callisto, an online reporting system for sexual assault.',
    long_description=long_description,
    license=license,
    author='Project Callisto',
    author_email='tech@projectcallisto.org',
    url='https://github.com/SexualHealthInnovations/callisto-core',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3',
    install_requires=[
        'django',
        'django-polymorphic>=1.0',
        'django-ratelimit>=1.0',
        'django-wizard-builder>=2.2,<2.3',
        'PyNaCl>=1.0',
        'python-gnupg>=0.4',
        'pytz>=2017',
        'reportlab>=3.0.0',
        'six',
        'argon2_cffi',
    ],
)
