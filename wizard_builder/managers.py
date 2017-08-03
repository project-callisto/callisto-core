import sys

from model_utils.managers import InheritanceManager, InheritanceQuerySet

from django.conf import settings
from django.contrib.sites.models import Site

# in addition to explicitly depending on django-model-utils,
# this code borrows in large part from django-polymorphic

# Portions of the below implementation are copyright django-polymorphic [Authors] contributors,
# and are under the BSD-3 Clause [License]
# Authors: https://github.com/django-polymorphic/django-polymorphic/blob/master/AUTHORS.rst
# License: https://github.com/django-polymorphic/django-polymorphic/blob/master/LICENSE


class PageBaseQuerySet(InheritanceQuerySet):

    def on_site(self, site_id=None):
        site_id = site_id or Site.objects.get_current().id
        return self.filter(
            sites__id__in=[site_id],
        )


class FormQuestionQuerySet(InheritanceQuerySet):
    pass


class AutoDowncastingManager(InheritanceManager):

    def get_queryset(self):
        base_queryset = self._queryset(self.model, using=self._db)
        if getattr(settings, 'WIZARD_BUILDER_DISABLE_DOWNCASTING', False):
            return base_queryset
        # sourced from similar code in django-polymorphic
        elif len(sys.argv) > 1 and sys.argv[1] == 'dumpdata':
            return base_queryset
        else:
            return base_queryset.select_subclasses()


class QuestionPageManager(AutoDowncastingManager):
    _queryset = PageBaseQuerySet

    def on_site(self, site_id=None):
        return self.get_queryset().on_site(site_id)


class FormQuestionManager(AutoDowncastingManager):
    _queryset = FormQuestionQuerySet
