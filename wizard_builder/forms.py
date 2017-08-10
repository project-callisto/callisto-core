from django import forms
from django.contrib.auth import get_user_model

from .models import Page

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
