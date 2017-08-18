History
-------

0.5.4 (2017-08-18)
++++++++++++++++++

* Refactor wizard views into a FormView
* remove all django-formtools legacy code
* added fixtures and template defaults
* added some heroku setup management commands
* include tests in release

    https://github.com/SexualHealthInnovations/django-wizard-builder/pull/118
    https://github.com/SexualHealthInnovations/django-wizard-builder/pull/120
    https://github.com/SexualHealthInnovations/django-wizard-builder/pull/125

0.3.2 (2017-08-07)
++++++++++++++++++

* add wizard form templates
* remove SingleLineTextWithMap, MultiLineText, Date
* add Choice extra widgets
* add django-widget-tweaks dependency

    https://github.com/SexualHealthInnovations/django-wizard-builder/pull/112

0.3.1 (2017-08-04)
++++++++++++++++++

* pypi cleanup release

0.3.0 (2017-08-03)
++++++++++++++++++

* remove models.PageBase, TextPage, Conditional
* rename models.QuestionPage to models.Page
* remove formtools dependency
* add django-tinymce4-lite dependency

    https://github.com/SexualHealthInnovations/django-wizard-builder/pull/95

0.2.1 (2017-06-12)
++++++++++++++++++

* change models.PageBase.site to models.PageBase.sites

    https://github.com/SexualHealthInnovations/django-wizard-builder/pull/72

0.1.2 (2017-05-16)
++++++++++++++++++

* pypi cleanup

    https://github.com/SexualHealthInnovations/django-wizard-builder/pull/49

0.1.1 (2017-05-16)
++++++++++++++++++

* add dumpdata downcasting disable hack

    https://github.com/SexualHealthInnovations/django-wizard-builder/pull/44

0.1.0 (2017-05-16)
++++++++++++++++++

* remove django-polymorphic, and replace it with django-model-utils

    https://github.com/SexualHealthInnovations/django-wizard-builder/pull/40

0.0.9 (2017-04-27)
++++++++++++++++++

* Add request domain support

0.0.1 (2016-05-16)
++++++++++++++++++

* First release on PyPI.
