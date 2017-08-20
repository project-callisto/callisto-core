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

.. |python36| image:: https://img.shields.io/badge/python-3.6-green.svg
   :alt: Python 3.6

.. |django111| image:: https://img.shields.io/badge/django-1.11-yellowgreen.svg
   :alt: Django 1.11

+--------------+--------------+
| Status       | Support      |
+==============+==============+
| |travis|     | |python36|   |
+--------------+--------------+
| |pypi|       | |django111|  |
+--------------+--------------+
| |climate|    |              |
+--------------+--------------+

Installation
-------------

django settings

::

    INSTALLED_APPS = [
      'django.contrib.sites',
      'nested_admin',
      'tinymce',
      'widget_tweaks',
      'wizard_builder',
    ]

urls.py

::

    urlpatterns = [
      url(r'^nested_admin/', include('nested_admin.urls')),
      url(r'^tinymce/', include('tinymce.urls')),
      url(r'^admin/', admin.site.urls),
    ]


Developement
-------------

setup

::

    $ pip install -r requirements.txt --upgrade
    $ make app-setup


cleanup / linting / tests

::

    $ make clean-lint
    $ make test-fast
