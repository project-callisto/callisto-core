from django import forms
from django.forms import widgets as django_widgets
from django.utils.safestring import mark_safe

from . import widgets as wizard_builder_widgets


class QuestionField(object):

    @classmethod
    def singlelinetext(cls, question):
        return forms.CharField(
            label=mark_safe(question.text),
            required=False,
        )

    @classmethod
    def textarea(cls, question):
        return forms.CharField(
            widget=forms.Textarea,
            label=mark_safe(question.text),
            required=False,
        )

    @classmethod
    def checkbox(cls, question):
        return forms.MultipleChoiceField(
            choices=question.choices_field_display,
            label=question.text,
            help_text=question.descriptive_text,
            required=False,
            widget=wizard_builder_widgets.CheckboxExtraSelectMultiple,
        )

    @classmethod
    def radiobutton(cls, question):
        if question.data.get('is_dropdown'):
            widget = django_widgets.Select
        else:
            widget = wizard_builder_widgets.RadioExtraSelect
        return forms.ChoiceField(
            choices=question.choices_field_display,
            label=question.text,
            help_text=question.descriptive_text,
            required=False,
            widget=widget,
        )
