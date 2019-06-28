import logging

from django.forms.fields import ChoiceField, Field
from django.forms.widgets import CheckboxSelectMultiple, RadioSelect, Select, TextInput

logger = logging.getLogger(__name__)


def conditional_id(choice):
    pk = choice.get("pk")
    return f"choice_{pk}"


def options_as_choices(data):
    return [
        (option.get("pk"), option.get("text")) for option in data.get("options", [])
    ]


def conditional_field_from_choice(choice):
    if choice.get("options"):
        return ConditionalField.dropdown(choice)
    elif choice.get("extra_info_text"):
        return ConditionalField.textinfo(choice)


class ConditionalField(object):
    @classmethod
    def dropdown(cls, choice):
        attrs = {
            "class": "extra-widget extra-widget-dropdown",
            "style": "display: none;",
        }
        return ChoiceField(
            required=False,
            choices=options_as_choices(choice),
            widget=Select(attrs=attrs),
        )

    @classmethod
    def textinfo(cls, choice):
        attrs = {
            "placeholder": choice.get("extra_info_text"),
            "class": "extra-widget extra-widget-text",
            "style": "display: none;",
        }
        return Field(required=False, widget=TextInput(attrs=attrs))


class ConditionalGenerator(object):
    """
        generates the "context" data needed to render a conditional
    """

    dropdown_var = "extra_dropdown_widget_context"
    text_var = "extra_text_widget_context"

    @classmethod
    def generate_context(cls, choice, querydict):
        self = cls()
        self.choice = choice
        self.querydict = querydict
        return self.context_from_conditional_type()

    def context_from_conditional_type(self):
        if self.choice.get("options"):
            field = ConditionalField.dropdown(self.choice)
            return {self.dropdown_var: self.context_from_field(field)}
        elif self.choice.get("extra_info_text"):
            field = ConditionalField.textinfo(self.choice)
            return {self.text_var: self.context_from_field(field)}
        else:
            return {}

    def context_from_field(self, field):
        name = conditional_id(self.choice)
        value = field.widget.value_from_datadict(self.querydict, None, name)
        return field.widget.get_context(name, value, {})


class ConditionalSelectMixin:
    """
        hooks into a Select widget, and adds conditionals to certain choices
    """

    option_template_name = "wizard_builder/input_option_extra.html"

    def value_from_datadict(self, data, files, name):
        """
            grab the querydict for use in create_option later
        """
        self.querydict = data
        return super().value_from_datadict(data, files, name)

    def create_option(self, *args, **kwargs):
        """
            add the created option, our conditional field
        """
        option = super().create_option(*args, **kwargs)
        conditional_context = ConditionalGenerator.generate_context(
            choice=self.choice_datas[int(option["index"])], querydict=self.querydict
        )
        option.update(conditional_context)
        return option


class ConditionalSelect(ConditionalSelectMixin, Select):
    """
        A dropdown with conditional fields
    """

    pass


class RadioConditionalSelect(ConditionalSelectMixin, RadioSelect):
    """
        A radio button series with conditional fields
    """

    pass


class CheckboxConditionalSelectMultiple(ConditionalSelectMixin, CheckboxSelectMultiple):
    """
        A checkbox series with conditional fields
    """

    pass
