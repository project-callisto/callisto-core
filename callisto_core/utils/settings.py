from callisto_core.utils.settings_django_init import *

from callisto_core.tests.utils import api as test_api

CALLISTO_MATCHING_API = test_api.CustomMatchingApi
CALLISTO_NOTIFICATION_API = test_api.CustomNotificationApi
