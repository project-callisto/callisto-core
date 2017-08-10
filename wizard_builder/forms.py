from django import forms
from django.contrib.auth import get_user_model

from .models import Page

# rearranged from django-formtools

# Portions of the below implementation are copyright theDjango Software Foundation and individual contributors, and
# are under the BSD-3 Clause License:
# https://github.com/django/django-formtools/blob/master/LICENSE

User = get_user_model()


class PageForm(forms.Form):
    sections = dict(Page.SECTION_CHOICES)

    @property
    def serialized(self):
        return [
            question.serialized
            for question in self.page.questions
        ]

    @classmethod
    def setup(cls, page, page_index, section_map):
        cls.base_fields = {
            question.field_id: question.make_field()
            for question in page.questions
        }
        self = cls({})
        self.page = page
        self.page_index = page_index
        self.section_map = section_map
        return self


class PageFormManager(object):

    def __init__(self, site_id):
        self.pages = Page.objects.on_site(site_id).all()

    @property
    def section_map(self):
        return {
            section: idx + 1
            for idx, page in enumerate(self.pages)
            for section, _ in Page.SECTION_CHOICES
            if page.section == section
        }

    @property
    def forms(self):
        return [
            PageForm.setup(page, idx, self.section_map)
            for idx, page in enumerate(self.pages)
        ]
