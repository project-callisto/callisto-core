from polymorphic.managers import PolymorphicManager

from django.contrib.sites.models import Site


class PageBaseManager(PolymorphicManager):

    def on_site(self, site_id=None):
        site_id = site_id or Site.objects.get_current().id
        return self.filter(
            site__id=site_id,
        )
