import sys

from model_utils.managers import InheritanceManager, InheritanceQuerySet

from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models.manager import Manager
from django.db.models.query import QuerySet


class FormManager(object):

    def __init__(self, site_id, **kwargs):
        self.get_pages(site_id, **kwargs)

    @property
    def section_map(self):
        from .models import Page
        return {
            section: idx + 1
            for idx, page in enumerate(self.pages)
            for section, _ in Page.SECTION_CHOICES
            if page.section == section
        }

    @property
    def forms(self):
        return [
            self._generate_form(index, page)
            for index, page in enumerate(self.pages)
        ]

    def get_pages(self, site_id, **kwargs):
        from .models import Page
        self.pages = Page.objects.on_site(site_id).all()

    def _generate_form(self, index, page):
        from .forms import PageForm
        FormClass = PageForm.setup(page)
        return self._generate_form_instance(index, FormClass)

    def _generate_form_instance(self, index, FormClass):
        form = FormClass(self._get_form_data(index))
        form.page = page
        form.page_index = index
        form.section_map = section_map
        return form

    def _get_form_data(self, index):
        return {}


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
