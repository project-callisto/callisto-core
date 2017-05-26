import logging

from six.moves.urllib.parse import parse_qs, urlsplit

logger = logging.getLogger(__name__)


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

facebook_only = {'Facebook profile URL': {'domains': ['facebook.com'],
                                  'validation': facebook_validation_function,
                                   'example': 'http://www.facebook.com/johnsmithfakename'}}
