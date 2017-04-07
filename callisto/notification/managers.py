from django.db.models.query import QuerySet
from django.contrib.sites.models import Site


class EmailNotificationQuerySet(QuerySet):

    def on_site(self, site_id=None):
        site_id = site_id or Site.objects.get_current().id
        return self.filter(
            sites__id__in=[site_id],
        )
