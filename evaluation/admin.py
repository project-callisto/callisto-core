from django.contrib import admin
from .models import EvalField
from reports.models import RecordFormItem, SingleLineText, MultiLineText, RadioButton, Date, Checkbox, SingleLineTextWithMap
from reports.admin import RecordFormItemParentAdmin, SingleLineTextAdmin, MultiLineTextAdmin, SingleLineTextWithMapAdmin, \
    RadioButtonAdmin, CheckboxAdmin, DateAdmin

class EvalFieldInline(admin.StackedInline):
    model = EvalField

class WithEval(object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inlines = (self.inlines or []) + [EvalFieldInline,]

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

class RecordFormItemsWithEvalParentAdmin(RecordFormItemParentAdmin):
    child_models = (
        (SingleLineText, SingleLineTextWithEvalAdmin),
        (MultiLineText, MultiLineTextWithEvalAdmin),
        (SingleLineTextWithMap, SingleLineTextWithMapWithEvalAdmin),
        (RadioButton, RadioButtonWithEvalAdmin),
        (Checkbox, CheckboxWithEvalAdmin),
        (Date, DateWithEvalAdmin),
    )

admin.site.unregister(RecordFormItem)
admin.site.register(RecordFormItem, RecordFormItemsWithEvalParentAdmin)
