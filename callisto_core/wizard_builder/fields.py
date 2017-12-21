import inspect

from django import forms
from django.utils.safestring import mark_safe

from . import widgets as wizard_builder_widgets


def get_field_options():
    '''
    Turns the field generating functions on QuestionField into a series
    of options

    Formatted to be consumed by Question.type.choices
    '''
    inspected_funcs = inspect.getmembers(
        QuestionField, predicate=inspect.ismethod)
    field_names = [
        (item[0], item[0])
        for item in inspected_funcs
    ]
    return field_names


class ConditionalFieldMixin:

    def __init__(self, *args, choice_datas, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget.choice_datas = choice_datas


class ConditionalChoiceField(
    ConditionalFieldMixin,
    forms.ChoiceField,
):
    pass


class ConditionalMultipleChoiceField(
    ConditionalFieldMixin,
    forms.MultipleChoiceField,
):
    pass


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
            required=False,
            label=mark_safe(question.text),
            help_text=mark_safe(question.descriptive_text),
        )

    @classmethod
    def textarea(cls, question):
        return forms.CharField(
            required=False,
            label=mark_safe(question.text),
            help_text=mark_safe(question.descriptive_text),
            widget=forms.Textarea,
        )

    @classmethod
    def checkbox(cls, question):
        return ConditionalMultipleChoiceField(
            required=False,
            auto_id=True,
            label=mark_safe(question.text),
            help_text=mark_safe(question.descriptive_text),
            widget=wizard_builder_widgets.CheckboxConditionalSelectMultiple,
            choices=question.choices_pk_text_array,
            choice_datas=question.choices_data_array,
        )

    @classmethod
    def radiobutton(cls, question):
        return ConditionalChoiceField(
            required=False,
            auto_id=True,
            label=mark_safe(question.text),
            help_text=mark_safe(question.descriptive_text),
            widget=wizard_builder_widgets.RadioConditionalSelect,
            choices=question.choices_pk_text_array,
            choice_datas=question.choices_data_array,
        )

    @classmethod
    def dropdown(cls, question):
        return ConditionalChoiceField(
            required=False,
            label=mark_safe(question.text),
            help_text=mark_safe(question.descriptive_text),
            widget=wizard_builder_widgets.ConditionalSelect,
            choices=question.choices_pk_text_array,
            choice_datas=question.choices_data_array,
        )
