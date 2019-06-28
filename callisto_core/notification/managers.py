from django.contrib.sites.models import Site
from django.db.models.query import QuerySet


class EmailNotificationQuerySet(QuerySet):
    def on_site(self, site_id=None):
        try:
            site_id = site_id or Site.objects.get_current().id
        except Site.DoesNotExist:
            site_id = 1
        return self.filter(sites__id__in=[site_id])
