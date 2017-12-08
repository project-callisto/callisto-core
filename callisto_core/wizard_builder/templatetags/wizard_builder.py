from widget_tweaks.templatetags.widget_tweaks import append_attr

from django import template
from django.forms.widgets import ChoiceWidget

register = template.Library()


# TODO: pull request against django-widget-tweaks ?
@register.filter(is_safe=True)
def add_aria_tags_to_field(field):
    attrs = []
    if field.help_text or field.label:
        attrs.append("aria-describedby:help-" + field.id_for_label)
    if field.field.required:
        attrs.append("aria-required:true")
    if field.errors:
        attrs.append("aria-invalid:true")
        attrs.append("aria-describedby:error-" + field.id_for_label)
    for attr in attrs:
        append_attr(field, attr)
    return field


# TODO: remove, replace with widget template
@register.filter(name='is_multiple_choice')
def is_multiple_choice(field):
    return issubclass(field.field.widget.__class__, ChoiceWidget)
