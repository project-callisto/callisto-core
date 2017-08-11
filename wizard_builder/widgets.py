import logging

from django.forms.fields import ChoiceField, Field
from django.forms.widgets import CheckboxSelectMultiple, RadioSelect, TextInput

logger = logging.getLogger(__name__)


class InputOptionExtraMixin(object):
    '''
        adds extra_options_field and extra_info_field inline with a Choice
        instance
    '''
    option_template_name = 'wizard_builder/input_option_extra.html'
    _dropdown_var = 'extra_dropdown_widget_context'
    _text_var = 'extra_text_widget_context'

    @property
    def _option_fields(self):
        return [
            (option.pk, option.text)
            for option in self._choice.options
        ]

    @property
    def _get_context_dropdown(self):
        '''
            render widget for choice.options
        '''
        field = ChoiceField(
            choices=self._option_fields,
            required=False,
            widget=ChoiceField.widget(attrs={
                'class': "extra-widget extra-widget-dropdown",
                'style': "display: none;",
            }),
        )
        return field.widget.get_context('extra_options', '', {})

    @property
    def _get_context_text(self):
        '''
            render widget for choice.extra_info_text
        '''
        field = Field(
            required=False,
            widget=TextInput(
                attrs={
                    'placeholder': self._choice.extra_info_text,
                    'class': "extra-widget extra-widget-text",
                    'style': "display: none;",
                },
            ),
        )
        return field.widget.get_context('extra_info', '', {})

    @property
    def _get_context(self):
        '''
            render context for any extra widgets this instance may have
        '''
        if self._choice.options and self._choice.extra_info_text:
            logger.error('''
                self.options and self.extra_info_text defined for Choice(pk={})
            '''.format(self._choice.pk))
            return {}
        elif self._choice.options:
            return {self._dropdown_var: self._get_context_dropdown}
        elif self._choice.extra_info_text:
            return {self._text_var: self._get_context_text}
        else:
            return {}

    def value_from_datadict(self, *args, **kwargs):
        print('value_from_datadict')
        print(args)
        print(kwargs)
        return super().value_from_datadict(*args, **kwargs)

    def create_option(self, *args, **kwargs):
        from .models import Choice
        options = super().create_option(*args, **kwargs)
        self._choice = Choice.objects.get(id=options['value'])
        options.update(self._get_context)
        print(options)
        print(vars(self))
        return options


class RadioExtraSelect(
    InputOptionExtraMixin,
    RadioSelect,
):
    '''
        A RadioSelect with inline widgets
    '''
    pass


class CheckboxExtraSelectMultiple(
    InputOptionExtraMixin,
    CheckboxSelectMultiple,
):
    '''
        A Checkbox with inline widgets
    '''
    pass
