=============================
django-wizard-builder
=============================

.. |travis| image:: https://travis-ci.org/SexualHealthInnovations/django-wizard-builder.png?branch=master
    :target: https://travis-ci.org/SexualHealthInnovations/django-wizard-builder
    :alt: Build status

.. |pypi| image:: https://img.shields.io/pypi/v/django-wizard-builder.svg
   :target: https://pypi.python.org/pypi/django-wizard-builder
   :alt: PyPI Version

.. |climate| image:: https://codeclimate.com/github/SexualHealthInnovations/django-wizard-builder/badges/gpa.svg
   :target: https://codeclimate.com/github/SexualHealthInnovations/django-wizard-builder
   :alt: Code Climate

.. |python34| image:: https://img.shields.io/badge/python-3.4-green.svg
   :alt: Python 3.4

.. |python35| image:: https://img.shields.io/badge/python-3.5-green.svg
   :alt: Python 3.5

.. |python36| image:: https://img.shields.io/badge/python-3.6-green.svg
   :alt: Python 3.6

.. |django111| image:: https://img.shields.io/badge/django-1.11-yellowgreen.svg
   :alt: Django 1.11

Create multi-page forms with branching logic from the Django admin, no code required.

+--------------+
| Status       |
+==============+
| |travis|     |
+--------------+
| |pypi|       |
+--------------+
| |climate|    |
+--------------+


+------------+-------------+
|         Support          |
+============+=============+
| |python34| |django111|   |
+--------------------------+
| |python35| |django111|   |
+--------------------------+
| |python36| |django111|   |
+--------------------------+

Developement
-------------

setup

::

    $ source $VENV/bin/activate
    $ pip install -r requirements/dev.txt


cleanup / linting / tests

::

    $ make clean-lint
    $ make test
    $ make test-all
