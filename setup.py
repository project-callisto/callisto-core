#!/usr/bin/env python
# -*- coding: utf-8 -*-
from wizard_builder import __version__ as version

from setuptools import setup, find_packages


try:
    import pypandoc
    long_description = pypandoc.convert_file('README.md', 'rst') + \
        pypandoc.convert_file('HISTORY.md', 'rst')
except BaseException:
    long_description = ''


setup(
    name='django-wizard-builder',
    version=version,
    description='Create multi-page forms from the Django admin',
    long_description=long_description,
    license="BSD",
    author='Project Callisto',
    author_email='tech@projectcallisto.org',
    url='https://github.com/SexualHealthInnovations/django-wizard-builder',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3',
    install_requires=[
        'django-model-utils>=3.0',
        'django-widget-tweaks==1.4.1',
        'django-nested-admin==3.0.20',
    ],
)
