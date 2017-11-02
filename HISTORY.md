# History / Changelog

## 2.5.2 (2017-11-02)

* re-enable conditionals

    https://github.com/project-callisto/django-wizard-builder/pull/205

## 2.5.1 (2017-10-30)

* fix migration 0034 on postgres

## 2.5.0 (2017-10-28)

* removed downcasting queries
* removed django-model-utils dependency
* refactored admin classes

    https://github.com/project-callisto/django-wizard-builder/pull/200

## 2.4.4 (2017-10-28)

* fix button order in example app

## 2.4.3 (2017-10-20)

* partially disable conditionals

    https://github.com/project-callisto/django-wizard-builder/pull/198

## 2.4.2 (2017-10-19)

* answer display updates for [callisto-core data persistence PR](https://github.com/project-callisto/callisto-core/pull/311)

    https://github.com/project-callisto/django-wizard-builder/pull/197

## 2.4.1 (2017-10-17)

* move field generating code out of the models

    https://github.com/project-callisto/django-wizard-builder/pull/196

## 2.4.0 (2017-10-17)

* question fields are now generated from session data, rather than being pulled from the database on each request

    https://github.com/project-callisto/django-wizard-builder/pull/192

## 2.3.0 (2017-10-12)

* add TextArea question type (s/o [@scattermagic](https://github.com/scattermagic))

    https://github.com/project-callisto/django-wizard-builder/pull/191

## 2.2.4 (2017-10-12)

* fix multiple choice answer display on review page (s/o [@scattermagic](https://github.com/scattermagic))

    https://github.com/project-callisto/django-wizard-builder/pull/187

## 2.2.3 (2017-09-19)

* fix a bug with incorrectly formatted review page answers

    https://github.com/SexualHealthInnovations/django-wizard-builder/pull/177

## 2.2.2 (2017-09-18)

* update tests for callisto's use case
* remove infobox

    https://github.com/SexualHealthInnovations/django-wizard-builder/pull/176

## 2.2.1 (2017-09-15)

* remove tinymce

## 2.1.0 (2017-09-14)

* views / view_partials / view_helpers cleanup
* WizardFormPartial moved from views.py to view_partials.py

    https://github.com/SexualHealthInnovations/django-wizard-builder/pull/169

## 2.0.0 (2017-09-12)

* disable WIP conditionals on review page
* update StorageHelper session api, which is now

  - StorageHelper.current_data_from_storage
  - StorageHelper.add_data_to_storage
  - StorageHelper.init_storage

        https://github.com/SexualHealthInnovations/django-wizard-builder/pull/164

## 1.0.6 (2017-09-06)

* show unanswered questions on the review page

## 1.0.2 (2017-08-22)

* add debug logging to wizard manager

## 1.0.0 (2017-08-20)

* first major release version
* lock api to callisto-core

    https://github.com/SexualHealthInnovations/django-wizard-builder/pull/125

## 0.5.5 (2017-08-18)

* Refactor wizard views into a FormView
* remove all django-formtools legacy code
* added fixtures and template defaults
* added some heroku setup management commands
* include tests in release

    https://github.com/SexualHealthInnovations/django-wizard-builder/pull/118
    https://github.com/SexualHealthInnovations/django-wizard-builder/pull/120
    https://github.com/SexualHealthInnovations/django-wizard-builder/pull/125

## 0.3.2 (2017-08-07)

* add wizard form templates
* remove SingleLineTextWithMap, MultiLineText, Date
* add Choice extra widgets
* add django-widget-tweaks dependency

    https://github.com/SexualHealthInnovations/django-wizard-builder/pull/112

## 0.3.1 (2017-08-04)

* pypi cleanup release

## 0.3.0 (2017-08-03)

* remove models.PageBase, TextPage, Conditional
* rename models.QuestionPage to models.Page
* remove formtools dependency
* add django-tinymce4-lite dependency

    https://github.com/SexualHealthInnovations/django-wizard-builder/pull/95

## 0.2.1 (2017-06-12)

* change models.PageBase.site to models.PageBase.sites

    https://github.com/SexualHealthInnovations/django-wizard-builder/pull/72

## 0.1.2 (2017-05-16)

* pypi cleanup

    https://github.com/SexualHealthInnovations/django-wizard-builder/pull/49

## 0.1.1 (2017-05-16)

* add dumpdata downcasting disable hack

    https://github.com/SexualHealthInnovations/django-wizard-builder/pull/44

## 0.1.0 (2017-05-16)

* remove django-polymorphic, and replace it with django-model-utils

    https://github.com/SexualHealthInnovations/django-wizard-builder/pull/40

## 0.0.9 (2017-04-27)

* Add request domain support

## 0.0.1 (2016-05-16)

* First release on PyPI.
