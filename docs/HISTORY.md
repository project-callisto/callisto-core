# History / Changelog

## 0.21.1 (2018-01-30)

* Moved celery to be loaded as worker, instead of fork
    * https://github.com/project-callisto/callisto-core/pull/403

## 0.21.0 (2018-01-29)

* Moved notification emails to celery
    * https://github.com/project-callisto/callisto-core/pull/369

## 0.20.17 (2018-01-26)

* remove duplicate '*' from forms
    * https://github.com/project-callisto/callisto-core/pull/401

## 0.20.16 (2018-01-25)

* remove passphrase requirement from reporting confirmation
    * https://github.com/project-callisto/callisto-core/pull/400

## 0.20.15 (2018-01-24)

* Added missing '*' to passphrase screens

## 0.20.14 (2018-01-24)

* added missing '*' for required fields
* fixed spelling error on matching form
    * https://github.com/project-callisto/callisto-core/pull/396

## 0.20.13 (2018-01-23)

* made `NotificationApi.ALERT_LIST` a property

## 0.20.12 (2018-01-23)

* fixed error display for matching and reporting flow
* fixed dashboard URL in navbar

## 0.20.10 (2018-01-18)

* use a single mail domain (in prod)

## 0.20.9 (2018-01-15)

* added "*" to required fields in matching form
* removed placeholder text from matching form fields
    * https://github.com/project-callisto/callisto-core/pull/390

## 0.20.8 (2018-01-15)

* added "*" to required fields in reporting forms
    * https://github.com/project-callisto/callisto-core/pull/389

## 0.20.7 (2018-01-15)

* NotificationApi patches
    * https://github.com/project-callisto/callisto-core/pull/385
    * https://github.com/project-callisto/callisto-core/pull/387

## 0.20.5 (2018-01-15)

* add a `<p>` tag to record form multiple choice labels

## 0.20.4 (2018-01-10)

* move wizard builder's site foreign key from `Page` to `FormQuestion`
    * https://github.com/project-callisto/callisto-core/pull/384

## 0.20.2 (2018-01-05)

* update notification api for campus-client's use case
* sync account view organization with delivery and reporting
    * https://github.com/project-callisto/callisto-core/pull/377

## 0.20.1 (2018-01-05)

* merge notification api from campus-client
    * https://github.com/project-callisto/callisto-core/pull/359
* add report and match alerting
    * https://github.com/project-callisto/callisto-core/pull/371
* update eval actions
    * https://github.com/project-callisto/callisto-core/pull/372

## 0.20.0 (2017-12-18)

* add callisto_core/accounts application

    https://github.com/project-callisto/callisto-core/pull/346

## 0.19.9 (2017-12-21)

* add basic celery setup

    https://github.com/project-callisto/callisto-core/pull/349

## 0.19.8 (2017-12-20)

* form html adjustments

    https://github.com/project-callisto/callisto-core/pull/355

## 0.19.7 (2017-12-18)

* eval data filtering is being moved to the stats frontend

    https://github.com/project-callisto/callisto-core/pull/357

## 0.19.6 (2017-12-15)

* the evaluation model is now used only for storing record actions
* callisto gpg key encrypted data is now stored on the record model
* delivery now has a model for storing callisto encrypted record data
    * (this was previously the functionality of eval's encrypted field)

    https://github.com/project-callisto/callisto-core/pull/356

## 0.19.5 (2017-12-14)

* add field for filtering eval data

    https://github.com/project-callisto/callisto-core/pull/354

## 0.19.4 (2017-12-13)

* template display update

    https://github.com/project-callisto/callisto-core/pull/352

## 0.19.3 (2017-12-13)

* wipe eval migrations, for better downstream support

## 0.19.2 (2017-12-13)

* add eval actions

## 0.19.1 (2017-12-11)

* change api classes (back) to importing from a settings string

## 0.19.0 (2017-12-08)

* merge django-wizard-builder into callisto-core
* !!! WARNING !!! this is an **immensely** breaking change

    https://github.com/project-callisto/callisto-core/pull/345

## 0.18.8 (2017-12-07)

* required feild display overrides

## 0.18.7 (2017-12-07)

* HTML error display adjustments

## 0.18.6 (2017-12-01)

* allow decryption of records that didn't get an encode prefix set

## 0.18.5 (2017-11-23)

* fix NotificationApi.get_cover_page incorrect attrs

## 0.18.4 (2017-11-23)

* add dashboard views, and update selenium tests
* add NotificationApi hooks

## 0.18.2 (2017-11-22)

* regenerate uuids, enforce their uniqueness

## 0.18.0 (2017-11-22)

* remove contenttypes dependency from delivery models

## 0.17.3 (2017-11-21)

* add sites middleware

## 0.17.2 (2017-11-21)

* resolve test path issues

## 0.17.1 (2017-11-20)

* resolve single EmailNotification when multiple present (and warn about this behavior)

## 0.17.0 (2017-11-20)

* rework `CallistoCoreMatchingApi`
* add `TenantApi`, `CallistoCoreTenantApi`
* moved the following attributes from `settings.VAR` to `TenantApi('VAR')`
    * `COORDINATOR_NAME`
    * `COORDINATOR_EMAIL`
    * `COORDINATOR_PUBLIC_KEY`
* this is a fairly thoroughly breaking version, so be sure to check all your corners

## 0.16.2 (2017-11-02)

* add a `site_id=1` fallback to `EmailNotification.objects.on_site`

## 0.16.1 (2017-10-28)

* bump version support to `django-wizard-builder>=2.5,<2.6`

## 0.16.0 (2017-10-19)

* better support for multiple records
* scope stored passphrase to current report uuid
* rename various view methods
    * `KeyResetTemplatePartial` => `PassphraseClearingPartial`
    * `clear_passphrase` => `clear_passphrases`
    * `set_passphrase` => `set_passphrase`
    * `passphrase` => `passphrase`
* remove `report_and_key_present`, as `passphrase` needs a report now

    https://github.com/project-callisto/callisto-core/pull/313

## 0.15.11 (2017-10-19)

* bugfixing record data updating (added in v0.15.8)

    https://github.com/project-callisto/callisto-core/pull/311

## 0.15.10 (2017-10-17)

* bump version support to `django-wizard-builder>=2.4,<2.5`

## 0.15.9 (2017-10-17)

* bump version support to `django-wizard-builder>=2.3,<2.4`
* add TextArea to eval (note: eval is currently disabled)

    https://github.com/project-callisto/callisto-core/pull/308

## 0.15.8 (2017-10-13)

* add functionality for updating the data format of records

    https://github.com/project-callisto/callisto-core/pull/303

## 0.15.7 (2017-10-08)

* fix email notification admin (s/o [@lisac](https://github.com/lisac))

    https://github.com/project-callisto/callisto-core/pull/301

## 0.15.6 (2017-10-06)

* fix form error displaying in submission flow

    https://github.com/project-callisto/callisto-core/pull/299

## 0.15.5 (2017-10-05)

* all pdf datetimes now display in a human readable format

    https://github.com/project-callisto/callisto-core/pull/298

## 0.15.4 (2017-10-05)

* the system now sends an email to all parties whenever a match is found

    https://github.com/project-callisto/callisto-core/pull/297

## 0.15.3 (2017-10-04)

* remove Report.autosaved
* update Report.last_edited on save

    https://github.com/project-callisto/callisto-core/pull/296

## 0.15.2 (2017-10-03)

* added a hook for using different types of validators in the matching flow

    https://github.com/project-callisto/callisto-core/pull/295

## 0.15.1 (2017-09-22)

* fix match report notifications

    https://github.com/project-callisto/callisto-core/pull/292

## 0.15.0 (2017-09-21)

* removed EmailNotification from delivery migrations

    https://github.com/project-callisto/callisto-core/pull/289

## 0.14.1 (2017-09-20)

* fix matching form, update model encryption docs

    https://github.com/project-callisto/callisto-core/pull/287

## 0.14.0 (2017-09-19)

* add `reporting_success_url` and `get_reporting_success_url`

    https://github.com/project-callisto/callisto-core/pull/284

## 0.13.3 (2017-09-14)

* General view fixes

    https://github.com/project-callisto/callisto-core/pull/280

## 0.13.2 (2017-09-14)

* Add distinct view and download PDF options

    https://github.com/project-callisto/callisto-core/pull/278

## 0.13.1 (2017-09-14)

* Fix some view issues introduced in v0.13.0

    https://github.com/project-callisto/callisto-core/pull/277

## 0.13.0 (2017-09-14)

* Clarified urls.py views.py vs view_partials.py vs view_helpers.py
* Moved view functions around to account for the above. See the respective files for an explaination

    https://github.com/project-callisto/callisto-core/pull/274

## 0.12.9 (2017-09-13)

* create an upgrade path for reports created before django wizard builder 2.0

    https://github.com/project-callisto/callisto-core/pull/273

## 0.12.8 (2017-09-12)

* update EncryptedStorageHelper for django wizard builder 2.0

    https://github.com/project-callisto/callisto-core/pull/272

## 0.12.7 (2017-09-08)

* fix delivery migration 0014, add delivery migration 0016

    https://github.com/project-callisto/callisto-core/pull/266

## 0.12.6 (2017-09-08)

* fix report action views

    https://github.com/project-callisto/callisto-core/pull/265

## 0.12.4 (2017-09-06)

* use updated wizard builder review page in report pdfs

    https://github.com/project-callisto/callisto-core/pull/263

## 0.12.2 (2017-09-05)

* refactor view inheritance, stabilize reporting and matching views
* un-pin dependencies

    https://github.com/project-callisto/callisto-core/pull/260
    https://github.com/project-callisto/callisto-core/pull/261

## 0.12.0 (2017-08-24)

* add reporting and matching views

    https://github.com/project-callisto/callisto-core/pull/251

## 0.11.0 (2017-08-21)

* update to wizard builder 1.0

## 0.10.12 (2017-08-20)

* new record form encryption process
* include requirements and tests in package

    https://github.com/project-callisto/callisto-core/pull/213

## 0.9.2 (2017-07-07)

* don't overwrite email domain if it's already set

    https://github.com/project-callisto/callisto-core/pull/213

## 0.9.1 (2017-07-06)

* update MatchingApi to match NotificationApi

    https://github.com/project-callisto/callisto-core/pull/212

## 0.9.0 (2017-07-06)

* NotificationApi update, allowing for more effective subclassing

    https://github.com/project-callisto/callisto-core/pull/210

## 0.8.2 (2017-07-03)

* add logging to email notifications

    https://github.com/project-callisto/callisto-core/pull/208

## 0.8.1 (2017-06-26)

* remove password entropy requirement

    https://github.com/project-callisto/callisto-core/pull/205

## 0.8.0 (2017-06-23)

* DeliveryApi => NotificationApi
* cleanup and normalize Api classes
* drop python 2 support
* drop django 1.8, 1.10 support
* callisto/ => callisto_core/
* add UUID to Report

    https://github.com/project-callisto/callisto-core/pull/123
    https://github.com/project-callisto/callisto-core/pull/202

## 0.7.0 (2017-06-13)

* update to django wizard builder version 0.2.1

## 0.6.7 (2017-06-12)

* fix version missing from pypi release

## 0.6.2 (2017-06-08)

* make django dependency explicit
* removed 'environ' dependency

    https://github.com/project-callisto/callisto-core/pull/191

## 0.6.1 (2017-06-08)

* install dependencies on pypi

    https://github.com/project-callisto/callisto-core/pull/184

## 0.6.0 (2017-06-01)

* Allow for custom matching identifiers
* Add a Twitter matching identifier validation

## 0.5.2 (2017-04-27)

* Update django wizard builder version

## 0.5.1 (2017-04-27)

* Don't auto-add settings.SITE_ID to newly created emails

    https://github.com/project-callisto/callisto-core/pull/172

## 0.5.0 (2017-04-27)

* Add support for getting the site_id from the request's domain

## 0.4.3 (2017-04-27)

* Added sites EmailNotification admin
* Added EmailNotification (name + sites) uniqueness validator

## 0.4.2 (2017-04-25)

* Fixed a bug with saving string SITE_IDs multiple times

## 0.4.1 (2017-04-25)

* Gave EmailNotification an id primary key

## 0.4.0 (2017-04-24)

* Introduced MatchingApi to allow customization of matching behavior
* Renamed many instances of "school" to "authority"

## 0.3.0 (2017-04-24)

* Moved EmailNotification from delivery to notification (may cause subtle bugs with migrations)

## 0.2.0 (2017-04-24)

* Added multi-tenant support (via django's sites framework) for EmailNotification

## 0.1.1 (2016-10-24)

* First release on PyPI.
