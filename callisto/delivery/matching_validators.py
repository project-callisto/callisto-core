import logging
from collections import OrderedDict

from six.moves.urllib.parse import parse_qs, urlsplit

logger = logging.getLogger(__name__)


def twitter_validation_function(url):
        url_parts = urlsplit(url)
        # check if acceptable domain
        domain = url_parts[1]
        if not (domain == 'twitter.com' or domain == 'www.twitter.com' or domain == 'mobile.twitter.com'):
            return None
        path = url_parts[2].strip('/').split('/')[0]
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
        if not path or path == "" or path in generic_twitter_urls:
            return None
        else:
            return path

twitter_validation_info = {'validation': twitter_validation_function,
                           'example': 'https://twitter.com/twitter_handle'}


def facebook_validation_function(url):
        url_parts = urlsplit(url)
        # check if acceptable domain
        domain = url_parts[1]
        if not (domain == 'facebook.com' or domain.endswith('.facebook.com')):
            return None
        path = url_parts[2].strip('/').split('/')[0]
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
            'games']
        if path == "profile.php":
            path = parse_qs(url_parts[3]).get('id')[0]
        if not path or path == "" or path.endswith('.php') or path in generic_fb_urls:
            return None
        else:
            return path

facebook_validation_info = {'validation': facebook_validation_function,
                            'example': 'http://www.facebook.com/johnsmithfakename'}

facebook_only = OrderedDict([('Facebook profile URL', facebook_validation_info)])
twitter_only = OrderedDict([('Twitter profile URL', twitter_validation_info)])
facebook_or_twitter = OrderedDict([('Facebook profile URL', facebook_validation_info),
                                   ('Twitter profile URL', twitter_validation_info)])
