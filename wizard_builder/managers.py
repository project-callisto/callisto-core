import sys

from model_utils.managers import InheritanceManager, InheritanceQuerySet

from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models.manager import Manager
from django.db.models.query import QuerySet

from .forms import PageForm
from .models import Page


class FormManager(object):
    model_class = Page
    form_class = PageForm

    def __init__(self, site_id, **kwargs):
        self.get_pages(site_id, **kwargs)

    def get_pages(self, site_id, **kwargs):
        self.pages = self.model_class.objects.on_site(site_id).all()

    @property
    def section_map(self):
        return {
            section: idx + 1
            for idx, page in enumerate(self.pages)
            for section, _ in self.model_class.SECTION_CHOICES
            if page.section == section
        }

    @property
    def forms(self):
        return [
            self.form_class.setup(page, idx, self.section_map)
            for idx, page in enumerate(self.pages)
        ]


class PageQuerySet(QuerySet):

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


class PageManager(Manager):
    _queryset_class = PageQuerySet

    def on_site(self, site_id=None):
        return self.get_queryset().on_site(site_id)


class FormQuestionManager(AutoDowncastingManager):
    _queryset = FormQuestionQuerySet
