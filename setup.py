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
    license=license,
    long_description=readme + '\n\n' + history,
    author='Sexual Health Innovations',
    author_email='tech@sexualhealthinnovations.org',
    url='https://github.com/SexualHealthInnovations/callisto-core',
    download_url='https://github.com/SexualHealthInnovations/callisto-core/tarball/release-8.15.16-2/',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'django',
        'django-polymorphic==1.2',
        'django-ratelimit==1.0.1',
        'django-wizard-builder==0.5.11',
        'PyNaCl==1.1.2',
        'python-gnupg==0.4.1',
        'pytz==2017.2',
        'reportlab==3.4.0',
        'six',
        'argon2_cffi',
    ],
    zip_safe=False,
    keywords='callisto-core',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.10',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
