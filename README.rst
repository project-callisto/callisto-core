=============================
django-wizard-builder
=============================

.. image:: https://travis-ci.org/SexualHealthInnovations/django-wizard-builder.png?branch=master
    :target: https://travis-ci.org/SexualHealthInnovations/django-wizard-builder
    :alt: Build status

.. image:: https://img.shields.io/pypi/v/django-wizard-builder.svg
   :target: https://pypi.python.org/pypi/django-wizard-builder
   :alt: PyPI Version

.. image:: https://codeclimate.com/github/SexualHealthInnovations/django-wizard-builder/badges/gpa.svg
   :target: https://codeclimate.com/github/SexualHealthInnovations/django-wizard-builder
   :alt: Code Climate

Create multi-page forms with branching logic from the Django admin, no code required.

Documentation
-------------

The full documentation will eventually be at https://django-wizard-builder.readthedocs.org.

Quickstart
----------

Install django-wizard-builder::

    pip install django-wizard-builder

Then use it in a project::

    import wizard_builder

Developement
-------------

setup

::

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install -r requirements/dev.txt


cleanup / linting / tests

::

    (myenv) $ make clean-lint
    (myenv) $ make test
    (myenv) $ make test-all


Credits
---------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage
