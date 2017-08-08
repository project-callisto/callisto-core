from django.forms.widgets import RadioSelect, CheckboxSelectMultiple


class RadioExtraSelect(RadioSelect):
    option_template_name = 'wizard_builder/input_option_extra.html'

class CheckboxExtraSelectMultiple(CheckboxSelectMultiple):
    option_template_name = 'wizard_builder/input_option_extra.html'
