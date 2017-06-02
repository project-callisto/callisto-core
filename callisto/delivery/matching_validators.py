import logging
from collections import OrderedDict

from six.moves.urllib.parse import parse_qs, urlsplit

from django.core.exceptions import ValidationError
from django.forms import URLField

logger = logging.getLogger(__name__)


def _clean_url(url):
    url_field = URLField()
    return url_field.clean(url.strip())


def _get_url_parts(url):
    url = _clean_url(url)
    return urlsplit(url)


def _get_initial_path(url_parts):
    return url_parts[2].strip('/').split('/')[0].lower()


generic_twitter_urls = [
        'i',
        'following',
        'followers',
        'who_to_follow',
        'settings',
        'search',
        'tos',
        'privacy',
        'about',
    ]


def twitter_validation_function(value):
        path = None
        try:
            url_parts = _get_url_parts(value)
            # check if acceptable domain
            domain = url_parts[1]
            if not (domain == 'twitter.com' or domain == 'www.twitter.com' or domain == 'mobile.twitter.com'):
                return None
            path = _get_initial_path(url_parts)
        except ValidationError:
            if value.startswith('@'):
                path = value[1:]
        # TODO: validate against allowed username characters
        # https://github.com/SexualHealthInnovations/callisto-core/issues/181
        if not path or path == "" or len(path) > 15 or path in generic_twitter_urls:
            return None
        else:
            return path


twitter_validation_info = {'validation': twitter_validation_function,
                           'example': 'https://twitter.com/twitter_handle or @twitter_handle',
                           'unique_prefix': 'twitter'}


generic_fb_urls = [
    'messages',
    'hashtag',
    'events',
    'pages',
    'groups',
    'bookmarks',
    'lists',
    'developers',
    'topic',
    'help',
    'privacy',
    'campaign',
    'policies',
    'support',
    'settings',
    'games',
    'people',]


def facebook_validation_function(url):
        try:
            url_parts = _get_url_parts(url)
            # check if acceptable domain
            domain = url_parts[1]
            if not (domain == 'facebook.com' or domain.endswith('.facebook.com')):
                return None
            path = _get_initial_path(url_parts)

            # old style numeric profiles
            if path == "profile.php":  # ex. https://www.facebook.com/profile.php?id=100010279981469
                path = parse_qs(url_parts[3]).get('id')[0]
            if path == 'people':  # ex. https://www.facebook.com/people/John-Doe/100013326345115
                path = url_parts[2].strip('/').split('/')[2].lower()

            # TODO: validate against allowed username characteristics
            # https://github.com/SexualHealthInnovations/callisto-core/issues/181
            if not path or path == "" or path.endswith('.php') or path in generic_fb_urls:
                return None
            else:
                return path
        except ValidationError:
            return None


'''
 NOTE: because identifiers are irreversibly encrypted and Facebook was the original matching identifier, Facebook
 identifiers are stored plain, with the prefix "www.facebook.com/" stripped. All other identifiers should be prefixed
 to allow for global uniqueness from Facebook profile identifiers.
'''
facebook_validation_info = {'validation': facebook_validation_function,
                            'example': 'http://www.facebook.com/johnsmithfakename',
                            'unique_prefix': ''}

'''
    potential options for identifier_domain_info, used in SubmitToMatchingForm
    identifier_domain_info is an ordered dictionary of matching identifiers
        key:
            the type of identifier requested
                example: 'Facebook profile URL' for Facebook
        value:
            a dictionary with
                a globally unique prefix (see note about Facebook's) to avoid cross-domain matches
                a validation function
                    should return None for invalid entries & return a minimal unique (within domain) path for valid
                an example input

    will return on first valid option tried
    see MatchingValidation.facebook_only (default)
'''

facebook_only = OrderedDict([('Facebook profile URL', facebook_validation_info)])
twitter_only = OrderedDict([('Twitter username/profile URL', twitter_validation_info)])
facebook_or_twitter = OrderedDict([('Facebook profile URL', facebook_validation_info),
                                   ('Twitter username/profile URL', twitter_validation_info)])
