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
            self.items[field_name].serialize_for_report(answer)
            for field_name, answer in self.cleaned_data.items()
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_tooltip = False
        # TODO: there is almost certainly a django builtin for this
        for question in self.items:
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
        # TODO: smell this type
        FormType = type(
            'Page{}Form'.format(idx),
            (PageForm,),
            {
                "items": page.questions,
                "infobox": page.infobox,
                "page_section": page.section,
                "section_map": section_map,
                "page_index": idx,
            },
        )
        if page.multiple:
            FormSet = formset_factory(FormType, extra=0, min_num=1)
            FormSetType = type(
                FormSet.__name__,
                (FormSet,),
                {
                    "sections": dict(Page.SECTION_CHOICES),
                    "name_for_multiple": page.name_for_multiple,
                    "page_id": page.pk,
                    "page_section": page.section,
                    "section_map": section_map,
                    "page_index": idx,
                },
            )
            generated_forms.append(FormSetType)
        else:
            generated_forms.append(FormType)

    return generated_forms
