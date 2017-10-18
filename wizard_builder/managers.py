import logging
import sys

from model_utils.managers import InheritanceManager, InheritanceQuerySet

from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models.manager import Manager
from django.db.models.query import QuerySet

from . import forms, mocks, models

logger = logging.getLogger(__name__)


class FormManager(object):

    @classmethod
    def get_form_models(cls, form_data={}, answer_data={}, site_id=1):
        self = cls()
        self.form_data = form_data
        self.answer_data = answer_data
        self.site_id = site_id
        return self.forms

    @classmethod
    def get_serialized_forms(cls, site_id=1):
        forms = cls.get_form_models(site_id=site_id)
        return [
            form.serialized
            for form in forms
        ]

    @property
    def forms(self):
        return [
            self._create_form_with_metadata(page)
            for page in self.pages()
        ]

    def pages(self):
        if not self.form_data:
            return models.Page.objects.wizard_set(self.site_id)
        else:
            return self._pages_via_form_data()

    def _create_form_with_metadata(self, page):
        form = self._create_cleaned_form(page, self.answer_data)
        form.page = page
        form.pk = page.pk
        return form

    def _create_cleaned_form(self, page, data):
        FormClass = forms.PageForm.setup(page)
        form = FormClass(data)
        form.full_clean()
        return form

    def _pages_via_form_data(self):
        pages = []
        for page_questions in self.form_data:
            page = mocks.MockPage(page_questions)
            pages.append(page)
        return pages


class PageQuerySet(QuerySet):

    def on_site(self, site_id=None):
        try:
            site_id = site_id or Site.objects.get_current().id
        except Site.DoesNotExist:
            site_id = 1
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
