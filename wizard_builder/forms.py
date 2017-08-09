from django import forms
from django.contrib.auth import get_user_model
from django.forms.formsets import formset_factory
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

    def setup(self):
        for question in self.page.questions:
            self.fields[question.field_id] = question.make_field()
            self.fields[question.field_id].help_text = mark_safe(
                question.descriptive_text + self.fields[question.field_id].help_text
            )


def get_form_pages(pages):
    generated_forms = []
    section_map = {}

    # TODO: smell this next
    for (section, _) in Page.SECTION_CHOICES:
        start = next((idx for idx, page in enumerate(
            pages) if page.section == section), None)
        section_map[section] = start

    for idx, page in enumerate(pages):
        form = PageForm()
        for name, value in {
            "page": page,
            "page_index": idx,
            "section_map": section_map,
            # "items": page.questions,
            # "infobox": page.infobox,
            # "page_section": page.section,
        }.items():
            setattr(form, name, value)
        form.setup()
        generated_forms.append(form)

    return generated_forms
