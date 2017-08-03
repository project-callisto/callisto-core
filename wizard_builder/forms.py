from django import forms
from django.contrib.auth import get_user_model
from django.forms.formsets import formset_factory
from django.utils.safestring import mark_safe

from .models import Date, MultipleChoice, Page

# rearranged from django-formtools

# Portions of the below implementation are copyright theDjango Software Foundation and individual contributors, and
# are under the BSD-3 Clause License:
# https://github.com/django/django-formtools/blob/master/LICENSE

User = get_user_model()


class PageForm(forms.Form):
    sections = dict(Page.SECTION_CHOICES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_tooltip = False
        extra_fields = {}
        date_fields = []
        for item in self.items:
            question_id = 'question_%s' % item.pk
            self.fields[question_id] = item.make_field()
            self.fields[question_id].help_text = mark_safe(item.descriptive_text + self.fields[question_id].help_text)
            if isinstance(item, MultipleChoice):
                for idx, choice_with_extra in enumerate(item.get_choices()):
                    placeholder = choice_with_extra.extra_info_placeholder
                    if placeholder:
                        extra_dict = {}
                        extra_field = forms.CharField(required=False, max_length=500, label=placeholder)
                        id_for_extra_field = '%s_extra-%s' % (question_id, choice_with_extra.pk)
                        self.fields[id_for_extra_field] = extra_field
                        radio_button_name = "%s-%s" % (self.prefix, question_id)
                        extra_dict['radio_button_name'] = radio_button_name
                        extra_dict['extra_field_id'] = '%s-%s' % (self.prefix, id_for_extra_field)
                        extra_checked = "%s_%s" % (radio_button_name, idx)
                        extra_dict['extra_checked'] = extra_checked
                        extra_fields["id_%s" % extra_checked] = extra_dict
            if isinstance(item, Date):
                date_fields.append('id_%s-%s' % (self.prefix, question_id))
        if len(extra_fields) > 0:
            self.extra_fields = extra_fields
        if len(date_fields) > 0:
            self.date_fields = date_fields


def get_form_pages(pages):
    generated_forms = []
    section_map = {}
    # TODO: smell this code
    for (section, _) in Page.SECTION_CHOICES:
        start = next((idx for idx, page in enumerate(pages) if page.section == section), None)
        section_map[section] = start

    for idx, (page, item_set) in enumerate(pages):
        FormType = type(
            'Page{}Form'.format(idx),
            (PageForm,),
            {
                "items": sorted(item_set, key=lambda i: i.position),
                "infobox": page.infobox,
                "page_section": page.section,
                "section_map": section_map,
                "page_index": idx,
            },
        )
        if page.multiple:
            FormSet = formset_factory(FormType, extra=0, min_num=1)
            FormSetType = type(
                'FormSetForm',
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
