from django import forms
from django.contrib.auth import get_user_model

from . import widgets

User = get_user_model()


class PageForm(forms.Form):

    @classmethod
    def setup(cls, page):
        cls.base_fields = {
            question.field_id: question.make_field()
            for question in page.questions
        }
        return cls

    @property
    def sections(self):
        from .models import Page
        return dict(Page.SECTION_CHOICES)

    @property
    def serialized(self):
        return self.page.serialized_questions

    def _clean_fields(self):
        for name, field in self.fields.items():
            self.cleaned_data[name] = field.widget.value_from_datadict(
                self.data, self.files, self.add_prefix(name))
        self._clean_conditional_fields()

    def _clean_conditional_fields(self):
        for question in self.page.questions:
            for choice in question.choices:
                self._clean_if_choice_conditional(choice.data)

    def _clean_if_choice_conditional(self, choice):
        field = widgets.conditional_field_from_choice(choice)
        if field:
            name = widgets.conditional_id(choice)
            self.cleaned_data[name] = field.widget.value_from_datadict(
                self.data, self.files, name)
