from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class PageForm(forms.Form):

    @property
    def sections(self):
        from .models import Page
        return dict(Page.SECTION_CHOICES)

    @property
    def serialized(self):
        return [
            question.serialized
            for question in self.page.questions
        ]

    @classmethod
    def setup(cls, page):
        cls.base_fields = {
            question.field_id: question.make_field()
            for question in page.questions
        }
        return cls

    def _clean_data(self):
        for key, value in self.data.items():
            if (isinstance(value, list)) and (len(value) == 1):
                self.data[key] = value[0]

    def _clean_fields(self):
        for name, field in self.fields.items():
            self._clean_data()
            self.cleaned_data[name] = field.widget.value_from_datadict(
                self.data, self.files, self.add_prefix(name))
