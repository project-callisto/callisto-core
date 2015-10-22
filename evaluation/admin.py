from django.contrib import admin
from reports.admin import RecordFormItemParentAdmin
from reports.models import RecordFormItem
from .models import EvalField

class EvalFieldInline(admin.StackedInline):
    model = EvalField

class ExtendedRecordFormAdmin(RecordFormItemParentAdmin):
    inlines = RecordFormItemParentAdmin.inlines.append(EvalFieldInline)

admin.site.unregister(RecordFormItem)
admin.site.register(RecordFormItem, ExtendedRecordFormAdmin)
