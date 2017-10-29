from django.contrib import admin

from wizard_builder.admin import FormQuestionAdmin
from wizard_builder.models import FormQuestion

from .models import EvaluationField


class EvalFieldInline(admin.StackedInline):
    model = EvaluationField


class WithEval(object):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inlines = (self.inlines or []) + [EvalFieldInline, ]


class FormQuestionEvalAdmin(
    WithEval,
    FormQuestionAdmin,
):
    pass


admin.site.unregister(FormQuestion)
admin.site.register(FormQuestion, FormQuestionEvalAdmin)
