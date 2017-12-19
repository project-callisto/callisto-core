from django.conf import settings


class TempSiteID():
    '''
        with TempSiteID(1):
            ...
    '''

    def __init__(self, site_id):
        self.site_id_temp = site_id

    def __enter__(self):
        self.site_id_stable = getattr(settings, 'SITE_ID', None)
        settings.SITE_ID = self.site_id_temp

    def __exit__(self, *args):
        settings.SITE_ID = self.site_id_stable
