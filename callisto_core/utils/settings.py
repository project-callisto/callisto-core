from callisto_core.utils.settings_django_init import *

import callisto_core.tests.utils.api
import callisto_core.utils.tenant_api

CALLISTO_MATCHING_API = callisto_core.tests.utils.api.CustomMatchingApi
CALLISTO_NOTIFICATION_API = callisto_core.tests.utils.api.CustomNotificationApi
