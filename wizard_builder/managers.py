from django.contrib.sites.models import Site
from django.db.models.query import QuerySet


class PageBaseQuerySet(QuerySet):

    def on_site(self, site_id=None):
        site_id = site_id or Site.objects.get_current().id
        return self.filter(
            site__id=[site_id],
        )
