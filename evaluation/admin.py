from django.contrib import admin
from reports.admin import RecordFormItemChildAdmin
from reports.models import RecordFormItem
from .models import EvalField

class EvalFieldInline(admin.StackedInline):
    model = EvalField

class ExtendedRecordFormAdmin(RecordFormItemChildAdmin):
    inlines = (EvalFieldInline,)

admin.site.unregister(RecordFormItem)
admin.site.register(RecordFormItem, ExtendedRecordFormAdmin)
