#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import sys

from callisto.delivery import __version__

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def get_version(*file_paths):
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    version_file = open(filename).read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')

version = get_version('callisto', 'delivery', '__init__.py')

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

print("Converting README from markdown to restructured text")
try:
    import pypandoc
    readme = pypandoc.convert_file('README.md', 'rst')
except (IOError, ImportError):
    print("Please install PyPandoc to allow conversion of the README")
    readme = open('README.md').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')
license = open('LICENSE').read()

setup(
    name='callisto-core',
    version=__version__,
    description="""Report intake, escrow, matching and secure delivery code for Callisto,
    an online reporting system for sexual assault.""",
    license=license,
    long_description=readme + '\n\n' + history,
    author='Sexual Health Innovations',
    author_email='tech@sexualhealthinnovations.org',
    url='https://github.com/SexualHealthInnovations/callisto-core',
    download_url='https://github.com/SexualHealthInnovations/callisto-core/tarball/release-8.15.16-2/',
    packages=[
        'callisto.delivery',
        'callisto.evaluation',
        'callisto.notification',
    ],
    include_package_data=True,
    install_requires=[],
    zip_safe=False,
    keywords='callisto-core',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
