import logging

from django.forms.fields import ChoiceField, Field
from django.forms.widgets import (
    CheckboxSelectMultiple, RadioSelect, Select, TextInput,
)

logger = logging.getLogger(__name__)


class ConditionalGenerator(object):
    dropdown_var = 'extra_dropdown_widget_context'
    text_var = 'extra_text_widget_context'

    @classmethod
    def generate_context(
        cls,
        choice,
        extra_info_data,
        extra_options_data,
    ):
        self = cls()
        self.choice = choice
        self.extra_info_data = extra_info_data
        self.extra_options_data = extra_options_data
        return self.context_from_conditional_type()

    def context_from_conditional_type(self):
        if self.choice.get('options'):
            return {self.dropdown_var: self.context_from_options_dropdown()}
        elif self.choice.get('extra_info_text'):
            return {self.text_var: self.context_from_extra_info()}
        else:
            return {}

    def dropdown_conditional_options(self):
        return [
            (option.get('pk'), option.get('text'))
            for option in self.choice.get('options')
        ]

    def context_from_options_dropdown(self):
        field = ChoiceField(
            choices=self.dropdown_conditional_options(),
            required=False,
            widget=ChoiceField.widget(attrs={
                'class': "extra-widget extra-widget-dropdown",
                'style': "display: none;",
            }),
        )
        return field.widget.get_context(
            'extra_options', self.extra_options_data, {})

    def context_from_extra_info(self):
        field = Field(
            required=False,
            widget=TextInput(
                attrs={
                    'placeholder': self.choice.get('extra_info_text'),
                    'class': "extra-widget extra-widget-text",
                    'style': "display: none;",
                },
            ),
        )
        return field.widget.get_context(
            'extra_info', self.extra_info_data, {})


class ConditionalSelectMixin:
    '''
        adds extra_options_field and extra_info_field inline with a Choice
        instance
    '''
    option_template_name = 'wizard_builder/input_option_extra.html'

    def value_from_datadict(self, *args, **kwargs):
        self.extra_info_data = args[0].get('extra_info', '')
        self.extra_options_data = args[0].get('extra_options', '')
        return super().value_from_datadict(*args, **kwargs)

    def create_option(self, *args, **kwargs):
        options = super().create_option(*args, **kwargs)
        options.update(
            ConditionalGenerator.generate_context(
                choice=self.choice_datas[int(options['index'])],
                extra_info_data=self.extra_info_data,
                extra_options_data=self.extra_options_data,
            )
        )
        return options


class ConditionalSelect(
    ConditionalSelectMixin,
    Select,
):
    '''
        A dropdown with conditional fields
    '''
    pass


class RadioConditionalSelect(
    ConditionalSelectMixin,
    RadioSelect,
):
    '''
        A radio button set with conditional fields
    '''
    pass


class CheckboxConditionalSelectMultiple(
    ConditionalSelectMixin,
    CheckboxSelectMultiple,
):
    '''
        A checkbox with conditional fields
    '''
    pass
