import sys

from model_utils.managers import InheritanceManager, InheritanceQuerySet

from django.conf import settings
from django.contrib.sites.models import Site


class DowncastingManagerMixin(object):

    def get_queryset(self):
        base_queryset = self._queryset(self.model, using=self._db)
        if getattr(settings, 'WIZARD_BUILDER_DISABLE_DOWNCASTING', False):
            return None
        elif len(sys.argv) > 1 and sys.argv[1] == 'dumpdata':
            return base_queryset
        else:
            return base_queryset.select_subclasses()


class PageBaseQuerySet(InheritanceQuerySet):

    def on_site(self, site_id=None):
        site_id = site_id or Site.objects.get_current().id
        return self.filter(
            site__id=site_id,
        )


class PageBaseManager(DowncastingManagerMixin, InheritanceManager):
    _queryset = PageBaseQuerySet

    def on_site(self, site_id=None):
        return self.get_queryset().on_site(site_id)


class FormQuestionQuerySet(InheritanceQuerySet):
    pass


class FormQuestionManager(DowncastingManagerMixin, InheritanceManager):
    _queryset = FormQuestionQuerySet
