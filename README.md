# django-wizard-builder

| Status | Support |
| --- | --- |
| [![Build Status][build-img]][build-url] | ![python 3.6][python36] |
| [![PyPI Version][pypi-img]][pypi-url] | ![django 1.11][django111] |

[build-img]: https://travis-ci.org/SexualHealthInnovations/django-wizard-builder.png?branch=master
[build-url]: https://travis-ci.org/SexualHealthInnovations/django-wizard-builder
[pypi-img]: https://img.shields.io/pypi/v/django-wizard-builder.svg
[pypi-url]: https://pypi.python.org/pypi/django-wizard-builder

[python36]: https://img.shields.io/badge/python-3.6-green.svg
[django111]: https://img.shields.io/badge/django-1.11-yellowgreen.svg


## Installation

django settings

    INSTALLED_APPS = [
        'django.contrib.sites',
        'nested_admin',
        'widget_tweaks',
        'wizard_builder',
    ]


urls.py

    urlpatterns = [
        url(r'^nested_admin/', include('nested_admin.urls')),
        url(r'^admin/', admin.site.urls),
    ]


## Developement

setup

    $ pip install -r requirements.txt --upgrade
    $ make app-setup


cleanup / linting / tests

    $ make clean-lint
    $ make test-fast
