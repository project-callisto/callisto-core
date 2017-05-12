from model_utils.managers import InheritanceManager, InheritanceQuerySet

from django.contrib.sites.models import Site
from django.db import models


class PageBaseQuerySet(InheritanceQuerySet):

    def on_site(self, site_id=None):
        site_id = site_id or Site.objects.get_current().id
        return self.filter(
            site__id=site_id,
        )


class PageBaseManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        base_queryset = PageBaseQuerySet(self.model, using=self._db)
        return base_queryset.select_subclasses()

    def on_site(self, site_id=None):
        return self.get_queryset().on_site(site_id)


class FormQuestionManager(InheritanceManager):
    use_for_related_fields = True

    def get_queryset(self):
        base_queryset = super(FormQuestionManager, self).get_queryset()
        return base_queryset.select_subclasses()
