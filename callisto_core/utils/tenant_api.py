from distutils.util import strtobool


def cast_string_to_type(
    value: str,
    cast: [str, bool, int]
) -> [str, bool, int]:
    '''
    reference implementation, not actually used in this repo
    '''
    if cast is str:
        return value
    elif cast is bool:
        return strtobool(value.lower())
    elif cast is int:
        return int(value)
    else:
        raise KeyError('Invalid `cast` param')


class CallistoCoreTenantApi(object):

    @staticmethod
    def site_settings(var, cast=str, request=None, site_id=None):
        '''
        api is locked to a similar function in a callisto campus private repo

        Implement this function to provide multi-tenant functionality for
        you application. You need to be able to derive your current tenant from
        either request or site_id (preferably both)

        an example implementation could look like:

        return {
            1: {
                'COORDINATOR_NAME': 'cat',
                'COORDINATOR_EMAIL': 'cat@example.com',
            },
            2: {
                'COORDINATOR_NAME': 'dog',
                'COORDINATOR_EMAIL': 'dog@example.com',
            },
        }[site_id][var]

        (callisto campus's implementation is a bit more complex than the above)

        takes a `cast` param to cast to that type
            cast params can be:
                str (the default)
                bool
                int
        '''
        return {
            'COORDINATOR_NAME': 'COORDINATOR_NAME',
            'COORDINATOR_EMAIL': 'COORDINATOR_EMAIL@example.com',
        }[var]
