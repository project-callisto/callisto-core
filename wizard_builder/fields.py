import inspect

from django import forms
from django.forms import widgets as django_widgets
from django.utils.safestring import mark_safe


def get_field_options():
    inspected_funcs = inspect.getmembers(QuestionField, predicate=inspect.ismethod)
    field_names = [
        (item[0], item[0])
        for item in inspected_funcs
    ]
    return field_names


class QuestionField(object):
    '''
    The functions on this class correspond to the types of questions
    you can use in the form wizard

    They are used to validate Question.type. So whenever you add / remove
    a field generating function, be sure to update the migrations
    '''

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
            widget=django_widgets.CheckboxSelectMultiple,
        )

    @classmethod
    def radiobutton(cls, question):
        if question.data.get('is_dropdown'):
            widget = django_widgets.Select
        else:
            widget = django_widgets.RadioSelect
        return forms.ChoiceField(
            choices=question.choices_field_display,
            label=question.text,
            help_text=question.descriptive_text,
            required=False,
            widget=widget,
        )
