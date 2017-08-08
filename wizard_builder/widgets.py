from django.forms.widgets import CheckboxSelectMultiple, RadioSelect


class InputOptionExtraMixin(object):
    option_template_name = 'wizard_builder/input_option_extra.html'


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
