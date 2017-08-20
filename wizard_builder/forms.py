from django import forms
from django.contrib.auth import get_user_model

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
        # TODO: serialize all the data required to generate questions
        return [
            question.serialized
            for question in self.page.questions
        ]

    def _clean_fields(self):
        for name, field in self.fields.items():
            self.cleaned_data[name] = field.widget.value_from_datadict(
                self.data, self.files, self.add_prefix(name))
