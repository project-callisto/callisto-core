.. :changelog:

History
-------

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

0.1.1 (2016-10-24)
++++++++++++++++++

* First release on PyPI.
