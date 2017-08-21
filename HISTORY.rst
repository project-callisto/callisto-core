.. :changelog:

History
-------

0.11.0 (2017-08-21)
++++++++++++++++++

* update to wizard builder 1.0

0.10.12 (2017-08-20)
++++++++++++++++++

* new record form encryption process
* include requirements and tests in package

    https://github.com/SexualHealthInnovations/callisto-core/pull/213

0.9.2 (2017-07-07)
++++++++++++++++++

* don't overwrite email domain if it's already set

    https://github.com/SexualHealthInnovations/callisto-core/pull/213

0.9.1 (2017-07-06)
++++++++++++++++++

* update MatchingApi to match NotificationApi

    https://github.com/SexualHealthInnovations/callisto-core/pull/212

0.9.0 (2017-07-06)
++++++++++++++++++

* NotificationApi update, allowing for me effective subclassing

    https://github.com/SexualHealthInnovations/callisto-core/pull/210

0.8.2 (2017-07-03)
++++++++++++++++++

* add logging to email notifications

    https://github.com/SexualHealthInnovations/callisto-core/pull/208

0.8.1 (2017-06-26)
++++++++++++++++++

* remove password entropy requirement

    https://github.com/SexualHealthInnovations/callisto-core/pull/205

0.8.0 (2017-06-23)
++++++++++++++++++

* DeliveryApi => NotificationApi
* cleanup and normalize Api classes
* drop python 2 support
* drop django 1.8, 1.10 support
* callisto/ => callisto_core/
* add UUID to Report

    https://github.com/SexualHealthInnovations/callisto-core/pull/123
    https://github.com/SexualHealthInnovations/callisto-core/pull/202

0.7.0 (2017-06-13)
++++++++++++++++++

* update to django wizard builder version 0.2.1

    https://github.com/SexualHealthInnovations/django-wizard-builder/blob/master/HISTORY.rst

0.6.7 (2017-06-12)
++++++++++++++++++

* fix version missing from pypi release

0.6.2 (2017-06-08)
++++++++++++++++++

* make django dependency explicit
* removed 'environ' dependency

    https://github.com/SexualHealthInnovations/callisto-core/pull/191

0.6.1 (2017-06-08)
++++++++++++++++++

* install dependencies on pypi

    https://github.com/SexualHealthInnovations/callisto-core/pull/184

0.6.0 (2017-06-01)
++++++++++++++++++

* Allow for custom matching identifiers
* Add a Twitter matching identifier validation

0.5.2 (2017-04-27)
++++++++++++++++++

* Update django wizard builder version

0.5.1 (2017-04-27)
++++++++++++++++++

* Don't auto-add settings.SITE_ID to newly created emails

    https://github.com/SexualHealthInnovations/callisto-core/pull/172

0.5.0 (2017-04-27)
++++++++++++++++++

* Add support for getting the site_id from the request's domain

0.4.3 (2017-04-27)
++++++++++++++++++

* Added sites EmailNotification admin
* Added EmailNotification (name + sites) uniqueness validator

0.4.2 (2017-04-25)
++++++++++++++++++

* Fixed a bug with saving string SITE_IDs multiple times

0.4.1 (2017-04-25)
++++++++++++++++++

* Gave EmailNotification an id primary key

0.4.0 (2017-04-24)
++++++++++++++++++

* Introduced MatchingApi to allow customization of matching behavior
* Renamed many instances of "school" to "authority"

0.3.0 (2017-04-24)
++++++++++++++++++

* Moved EmailNotification from delivery to notification (may cause subtle bugs with migrations)

0.2.0 (2017-04-24)
++++++++++++++++++

* Added multi-tenant support (via django's sites framework) for EmailNotification

0.1.1 (2016-10-24)
++++++++++++++++++

* First release on PyPI.
