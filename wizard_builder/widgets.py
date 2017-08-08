from django.forms.widgets import RadioSelect


class RadioExtraInfoSelect(RadioSelect):
    option_template_name = 'wizard_builder/forms/widgets/radio_extra_option.html'
