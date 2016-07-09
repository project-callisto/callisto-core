from wizard_builder.admin import (
    CheckboxAdmin, DateAdmin, FormQuestionParentAdmin, MultiLineTextAdmin,
    RadioButtonAdmin, SingleLineTextAdmin, SingleLineTextWithMapAdmin,
)
from wizard_builder.models import (
    Checkbox, Date, FormQuestion, MultiLineText, RadioButton, SingleLineText,
    SingleLineTextWithMap,
)

from django.contrib import admin

from .models import EvaluationField


class EvalFieldInline(admin.StackedInline):
    model = EvaluationField


class WithEval(object):

    def __init__(self, *args, **kwargs):
        super(WithEval, self).__init__(*args, **kwargs)
        self.inlines = (self.inlines or []) + [EvalFieldInline, ]


class SingleLineTextWithEvalAdmin(WithEval, SingleLineTextAdmin):
    pass


class MultiLineTextWithEvalAdmin(WithEval, MultiLineTextAdmin):
    pass


class SingleLineTextWithMapWithEvalAdmin(WithEval, SingleLineTextWithMapAdmin):
    pass


class RadioButtonWithEvalAdmin(WithEval, RadioButtonAdmin):
    pass


class CheckboxWithEvalAdmin(WithEval, CheckboxAdmin):
    pass


class DateWithEvalAdmin(WithEval, DateAdmin):
    pass


class FormQuestionsWithEvalParentAdmin(FormQuestionParentAdmin):
    child_models = (
        (SingleLineText, SingleLineTextWithEvalAdmin),
        (MultiLineText, MultiLineTextWithEvalAdmin),
        (SingleLineTextWithMap, SingleLineTextWithMapWithEvalAdmin),
        (RadioButton, RadioButtonWithEvalAdmin),
        (Checkbox, CheckboxWithEvalAdmin),
        (Date, DateWithEvalAdmin),
    )

admin.site.unregister(FormQuestion)
admin.site.register(FormQuestion, FormQuestionsWithEvalParentAdmin)
