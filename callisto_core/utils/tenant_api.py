from copy import copy
from distutils.util import strtobool


def cast_string_to_type(
    value: str,
    cast: [str, bool, int]
) -> [str, bool, int]:
    if cast is str:
        return value
    elif cast is bool:
        return strtobool(value)
    elif cast is int:
        return int(value)
    else:
        raise KeyError('Invalid `cast` param')


class CallistoCoreTenantApi(object):

    def get_current_domain(self):
        return 1

    @staticmethod
    def site_settings(var, cast=str, request=None, site_id=1):
        '''
        Implement this function to provide multi-tenant functionality for
        you application. You need to be able to derive your current tenant from
        either request or site_id (preferably both)

        The implementation here is a naive mock of a similar implementation in
        callisto campus

        Use like:
            from callisto_core.utils.tenant_api import TenantApi
            TenantApi.site_settings('SOME_NUMBER', cast=int, site_id=10)
        '''
        if request:
            try:
                site_id = request.site.id
            except BaseException:
                site_id = 1

        default_values = {
            'DISABLE_SIGNUP': 'False',
            'SCHOOL_SHORTNAME': 'callisto-core',
            'COORDINATOR_NAME': 'COORDINATOR_NAME',
            'COORDINATOR_EMAIL': 'COORDINATOR_EMAIL@example.com',
            'SCHOOL_EMAIL_DOMAIN': 'example.com',
            'COORDINATOR_PUBLIC_KEY': '''
-----BEGIN PGP PUBLIC KEY BLOCK-----
Comment: GPGTools - https://gpgtools.org

mQENBFdY2/0BCADse8jTgEgWtmHr3XkWVXh3zgxN2ubEI4sFXP4NK5yn8MVnFd2/
SdADsbZ7cCpVm2M/zAaEjbAK7Cvlomiuw2tuyT3EQrfLF9NHb7fIgANuA6VWquNO
wqOE/S/GzEYNtC/a0JqcYF82dzEb3ZvMhezvDuEwCfOEtrQV9sXUUEakQyo/0bRO
dLVuR/ralT9J0wb8RXE9dEkWE38mMgH/GFCIGen+l3gJJOYv/k3xlMcF+Uu7HOeZ
LT31CQIXQkMvUkcbvBKm5ynWvLbcfUcKX0L/YoCUbfd8Mf5KIg3rFMMJZWWOduuq
ePJN/Gcjv69CLB7quZSYSYP6s+1SyKv9HzjHABEBAAG0DWNhbGxpc3RvLWNvcmWJ
ATcEEwEKACEFAldY2/0CGwMFCwkIBwMFFQoJCAsFFgIDAQACHgECF4AACgkQ6+nJ
/nll+xyUaAgAvtQrBbHRPMviyIv5x8tLOYQeSdSZQ4OgNLYO6fQJkTdQX0p/OLCA
D2gSOj8pkzrwsh2OMXhuHaG2oUZzbChVy7ErkAN2UiWR1B9sV2IQ+A6F+ruXOjZO
M3cMlh/67gZQR7NfOFdsAjHATVcexHEWqfZAALl3Gt6jhxw9XpAzuAWnvGQSWFyg
7IE1r/MkFfsn56hbO4XMhDbiwENPtaTG1NUtJQLpykgfKgevSAOyKUEaLQwTf3iI
AQHnjf+0fR6p4Cj0QJFIADRzSxEcQ/tbXr9HDJct1w2wANrfSxwCxW/FDW/QpWqH
CyD4LzZm+C5DjSYuT06r7j/Wd6fuIqgcsrkBDQRXWNv9AQgAt7GEcgVIKmN/SCDA
UOY9VWib3VrXbpCg7Kwy54VDrC79WsZN5RmVIdjcTSzZz8xgfMSPtDrt6izp9WCz
tcRri+ont8uRNf5k/FPVG9Db5hZdTJS/kNspAOT8iuno4pmeihRvLEcFkvjC9tAM
eGMX4/CzOgcZLn81pekrfaLdRa62sl2S1w7UlU0JzsXf19IfGy6pXKMtE3a8APjH
JDI7cNyumPPXHR0Aksf4NRh5DjuwExKTQKP5yETWxRljPbump34PP5oHdIe36bGr
c2BAM7uRRWHz19PatFIeDOnICk8FcCK71aor7XCLlUta/iILQUeJd9YH92OwIHUw
7p8WmQARAQABiQEfBBgBCgAJBQJXWNv9AhsMAAoJEOvpyf55Zfsc55UH/i2NeMrZ
csE2gfoUsLmLYttVr5n1A4KH0qYL37NAqNq/IOQu3EvTSlyUk/r7Oi1qTYrxSKsB
1xCuyMYkjhzwFtAaN77XTd7YXqyMCNDM4DvPgVzAP/YV1xaDmcr3VG9K42JRL1EA
BnV6NcykEFwf+CCMHWX9R6zOSwurEMda6qNKdO5+wy2JOOl7IWe0IxgE3KDOmRdv
TpQMuo8A2LtGRdrWrl1C+17N30Zx7Xjy7zg8W8CkEPZEy3dPXZpH4HnV85tIKNk+
wcFlYKGBlea/REi7+EAtE0u/nX2FB6adtMwopHlyTonKURJnInM9/T0UAwiNxfAB
cL+QqgshFt79Yh0=
=3BvZ
-----END PGP PUBLIC KEY BLOCK-----
            ''',
        }

        defaults_with_signup_disabled = copy(default_values)
        defaults_with_signup_disabled['DISABLE_SIGNUP'] = 'True'

        site_values = {
            1: default_values,
            2: defaults_with_signup_disabled,
            3: default_values,
        }.get(site_id, {})

        value = site_values.get(var, '')
        value = cast_string_to_type(value, cast)

        return value
