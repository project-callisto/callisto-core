import logging
import sys

from model_utils.managers import InheritanceManager, InheritanceQuerySet

from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models.manager import Manager
from django.db.models.query import QuerySet

logger = logging.getLogger(__name__)


class FormManager(object):
    form_pk_field = 'form_pk_field'

    @classmethod
    def get_forms(cls, data={}, site_id=1):
        self = cls()
        self.data = data  # TODO: remove self.data, pass it down through funcs
        self.site_id = site_id
        return self.forms

    @property
    def section_map(self):
        # NOTE: function outdated
        from .models import Page
        return {
            section: idx + 1
            for idx, page in enumerate(self.pages())
            for section, _ in Page.SECTION_CHOICES
            if page.section == section
        }

    @property
    def forms(self):
        return [
            self._create_form_with_metadata(page)
            for page in self.pages()
        ]

    def form_pk(self, pk):
        return '{}_{}'.format(self.form_pk_field, pk)

    def pages(self):
        from .models import Page  # TODO: move to top
        return Page.objects.wizard_set(self.site_id)

    def _create_form_with_metadata(self, page):
        form = self._create_cleaned_form(page, self.data)
        form.page = page
        form.pk = page.pk
        form.section_map = self.section_map
        return form

    def _create_cleaned_form(self, page, data):
        from .forms import PageForm  # TODO: move to top
        FormClass = PageForm.setup(page)
        form = FormClass(data)
        form.full_clean()
        return form


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
