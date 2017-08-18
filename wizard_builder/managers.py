import sys

from model_utils.managers import InheritanceManager, InheritanceQuerySet

from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.db.models.manager import Manager
from django.db.models.query import QuerySet


class FormManager(object):

    @classmethod
    def get_forms(cls, view):
        return cls(view).forms

    def __init__(self, view):
        self.view = view

    @property
    def site_id(self):
        return get_current_site(self.view.request).id

    @property
    def section_map(self):
        # NOTE: function outdated
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
            self._create_form(index, page)
            for index, page in enumerate(self.pages)
        ]

    @property
    def pages(self):
        from .models import Page
        return Page.objects.wizard_set(self.site_id)

    def _create_form(self, index, page):
        from .forms import PageForm
        FormClass = PageForm.setup(page)
        return self._create_form_instance(
            FormClass, index, page)

    def _create_form_instance(self, FormClass, index, page):
        data = self._create_form_data(page)
        print('\tFormManager._create_form_instance.form.data', index, data)
        form = FormClass(**data)
        form.full_clean()
        form.page = page
        form.manager_index = index
        form.pk = page.pk
        form.section_map = self.section_map
        return form

    def _create_form_data(self, page):
        return {'data': self.view.storage.data_from_pk(page.pk)}


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

    def wizard_set(self, site_id=None):
        return self.on_site(site_id).order_by('position')

    def on_site(self, site_id=None):
        return self.get_queryset().on_site(site_id)


class FormQuestionManager(AutoDowncastingManager):
    _queryset = FormQuestionQuerySet
