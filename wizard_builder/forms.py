from django import forms
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe

from .models import Page

# rearranged from django-formtools

# Portions of the below implementation are copyright theDjango Software Foundation and individual contributors, and
# are under the BSD-3 Clause License:
# https://github.com/django/django-formtools/blob/master/LICENSE

User = get_user_model()


class PageForm(forms.Form):
    sections = dict(Page.SECTION_CHOICES)

    @property
    def processed(self):
        return [
            question.serialize_for_report(
                self.cleaned_data[question.field_id],
            )
            for question in self.page.questions
        ]

    @classmethod
    def setup(cls, page, page_index, section_map):
        cls.page = page
        cls.page_index = page_index
        cls.section_map = section_map
        self = cls()
        for question in self.page.questions:
            self.fields[question.field_id] = question.make_field()
            self.fields[question.field_id].help_text = mark_safe(
                question.descriptive_text + self.fields[question.field_id].help_text
            )
        return self


class PageFormManager(object):
    form_class = PageForm

    @classmethod
    def section_map(cls):
        # TODO: smell section_map
        _section_map = {}
        for (section, _) in Page.SECTION_CHOICES:
            start = next((idx for idx, page in enumerate(
                cls.pages) if page.section == section), None)
            _section_map[section] = start
        return _section_map

    @classmethod
    def items(cls):
        return {
            question.field_id: question
            for question in page.questions
            for page in cls.pages
        }

    @classmethod
    def forms(cls):
        return [
            cls.form_class.setup(page, idx, cls.section_map)
            for idx, page in enumerate(cls.pages)
        ]

    @classmethod
    def setup(cls, site_id):
        cls.pages = Page.objects.on_site(site_id).all()
        return cls.forms, cls.items
