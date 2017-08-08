from django.forms.widgets import CheckboxSelectMultiple, RadioSelect


class InputOptionExtraMixin(object):
    '''
        adds extra_options_field and extra_info_field inline with a Choice
        instance
    '''
    # TODO: add a hook into this template in django, instead of overwritting it
    option_template_name = 'wizard_builder/input_option_extra.html'

    def create_option(self, *args, **kwargs):
        from .models import Choice  # TODO: grab this class without an import
        options = super().create_option(*args, **kwargs)
        choice = Choice.objects.get(id=options['value'])
        options.update(choice.extra_widget_options)
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
