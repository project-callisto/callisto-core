import nested_admin

from .inlines import ChoiceInline


class FormQuestionAdmin(
    nested_admin.NestedModelAdmin,
):
    search_fields = ['short_str', 'type', 'page']
    list_filter = ['page__sites']
    inlines = [ChoiceInline]
