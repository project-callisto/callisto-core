#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import sys

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
    import pypandoc
    readme = pypandoc.convert_file('README.md', 'rst')
    print("Converting README from markdown to restructured text")
except (IOError, ImportError, OSError):
    print("Please install PyPandoc to allow conversion of the README")
    readme = open('README.md').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')
license = open('LICENSE').read()

setup(
    name='callisto-core',
    version=version,
    description='Report intake, escrow, matching and secure delivery code for Callisto, an online reporting system for sexual assault.',
    long_description=readme + '\n\n' + history,
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
        'django-polymorphic==1.3',
        'django-ratelimit==1.0.1',
        'django-wizard-builder==1.0.4',
        'PyNaCl==1.1.2',
        'python-gnupg==0.4.1',
        'pytz==2017.2',
        'reportlab==3.4.0',
        'six',
        'argon2_cffi',
    ],
)
