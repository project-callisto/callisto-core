import nested_admin

from django import forms

from .. import fields
from .inlines import ChoiceInline


class QuestionAdminForm(forms.ModelForm):
    type = forms.ChoiceField(choices=fields.get_field_options())


class FormQuestionAdmin(
    nested_admin.NestedModelAdmin,
):
    form = QuestionAdminForm
    search_fields = ['short_str', 'type', 'page']
    list_filter = ['sites']
    inlines = [ChoiceInline]
