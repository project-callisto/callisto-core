from distutils.util import strtobool
from django.contrib.sites.shortcuts import get_current_site


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

    @staticmethod
    def site_settings(var, cast=str, request=None, site_id=1):
        '''
        Implement this function to provide multi-tenant functionality for
        you application. You need to be able to derive your current tenant from
        either request or site_id (preferably both)

        The implementation here is a naive mock of a similar implementation in
        callisto campus

        Use like:
            TenantApi.site_settings('SOME_NUMBER', cast=int, site_id=10)
        '''
        if request:
            try:
                site_id = get_current_site(self.request).id
            except BaseException:
                site_id = 1

        site_values = {
            1: {
                'COORDINATOR_NAME': 'COORDINATOR_NAME',
                'COORDINATOR_EMAIL': 'COORDINATOR_EMAIL@example.com',
            }
        }.get(site_id, {})
        value = site_values.get(var, '')
        value = cast_string_to_type(value, cast)

        return value
