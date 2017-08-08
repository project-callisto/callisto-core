from django.forms.widgets import CheckboxSelectMultiple, RadioSelect


class InputOptionExtraMixin(object):
    # TODO: add a hook into this template, instead of overwritting it
    option_template_name = 'wizard_builder/input_option_extra.html'

    def create_option(self, *args, **kwargs):
        options = super().create_option(*args, **kwargs)
        choice_id = options['value']
        choice = self.attrs['choice_map'][choice_id]
        options = choice.add_extra_options(options)
        return options


class RadioExtraSelect(
    InputOptionExtraMixin,
    RadioSelect,
):
    pass


class CheckboxExtraSelectMultiple(
    InputOptionExtraMixin,
    CheckboxSelectMultiple,
):
    pass
