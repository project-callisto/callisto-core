from model_utils.managers import InheritanceQuerySet

from django.contrib.sites.models import Site


class PageBaseQuerySet(InheritanceQuerySet):

    def on_site(self, site_id=None):
        site_id = site_id or Site.objects.get_current().id
        return self.filter(
            site__id=site_id,
        )

class FormQuestionQuerySet(InheritanceQuerySet):

    pass
