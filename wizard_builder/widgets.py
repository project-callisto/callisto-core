import logging

from django.forms.fields import ChoiceField, Field
from django.forms.widgets import (
    CheckboxSelectMultiple, RadioSelect, Select, TextInput,
)

logger = logging.getLogger(__name__)


class ExtraOptionsGenerator(object):
    dropdown_var = 'extra_dropdown_widget_context'
    text_var = 'extra_text_widget_context'

    @classmethod
    def get_context(
        cls,
        choice,
        extra_info_data,
        extra_options_data,
    ):
        self = cls()
        self.choice = choice
        self.extra_info_data = extra_info_data
        self.extra_options_data = extra_options_data
        return self.create_context()

    def create_context(self):
        if self.choice.options and self.choice.extra_info_text:
            logger.error('''
                self.options and self.extra_info_text defined for Choice(pk={})
            '''.format(self.choice.pk))
            return {}
        elif self.choice.options:
            return {self.dropdown_var: self.get_context_dropdown()}
        elif self.choice.extra_info_text:
            return {self.text_var: self.get_context_text()}
        else:
            return {}

    def option_fields(self):
        return [
            (option.pk, option.text)
            for option in self.choice.options
        ]

    def get_context_dropdown(self):
        '''
            render widget for choice.options
        '''
        field = ChoiceField(
            choices=self.option_fields(),
            required=False,
            widget=ChoiceField.widget(attrs={
                'class': "extra-widget extra-widget-dropdown",
                'style': "display: none;",
            }),
        )
        return field.widget.get_context(
            'extra_options', self.extra_options_data, {})

    def get_context_text(self):
        '''
            render widget for choice.extra_info_text
        '''
        field = Field(
            required=False,
            widget=TextInput(
                attrs={
                    'placeholder': self.choice.extra_info_text,
                    'class': "extra-widget extra-widget-text",
                    'style': "display: none;",
                },
            ),
        )
        return field.widget.get_context(
            'extra_info', self.extra_info_data, {})


class InputOptionExtraMixin:
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
        from .models import Choice
        options = super().create_option(*args, **kwargs)
        options.update(ExtraOptionsGenerator.get_context(
            choice=Choice.objects.get(id=options['value']),
            extra_info_data=self.extra_info_data,
            extra_options_data=self.extra_options_data,
        ))
        return options


class ExtraSelect(
    InputOptionExtraMixin,
    Select,
):
    '''
        A dropdown with inline widgets
    '''
    pass


class RadioExtraSelect(
    InputOptionExtraMixin,
    RadioSelect,
):
    '''
        A radio button set with inline widgets
    '''
    pass


class CheckboxExtraSelectMultiple(
    InputOptionExtraMixin,
    CheckboxSelectMultiple,
):
    '''
        A checkbox with inline widgets
    '''
    pass
