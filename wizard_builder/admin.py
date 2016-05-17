from django.contrib import admin
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin
from .models import RecordFormItem, SingleLineText, MultiLineText, RadioButton, Choice, PageBase, RecordFormQuestionPage, \
                    RecordFormTextPage, Date, Checkbox, SingleLineTextWithMap, Conditional
#TODO: remove grappelli dependency
from grappelli.forms import GrappelliSortableHiddenMixin
from django.core.urlresolvers import reverse_lazy
from django.db import models
from django import forms


class RecordFormItemChildAdmin(PolymorphicChildModelAdmin):
    """ Base admin class for all child models """
    base_model = RecordFormItem

class SingleLineTextAdmin(RecordFormItemChildAdmin):
    base_model = SingleLineText

class MultiLineTextAdmin(RecordFormItemChildAdmin):
    base_model = MultiLineText

class SingleLineTextWithMapAdmin(RecordFormItemChildAdmin):
    base_model = MultiLineText

class ChoiceInline(GrappelliSortableHiddenMixin, admin.TabularInline):
    fields = ['text', 'position', 'extra_info_placeholder', 'id']
    model = Choice
    sortable_field_name = "position"
    extra = 0
    readonly_fields = ('id',)
    formfield_overrides = {
        models.TextField: {'widget': forms.TextInput},
    }

class RadioButtonAdmin(RecordFormItemChildAdmin):
    base_model =  RadioButton
    inlines = RecordFormItemChildAdmin.inlines + [
        ChoiceInline,
    ]
    exclude = ['example']

class CheckboxAdmin(RecordFormItemChildAdmin):
    base_model = Checkbox
    inlines = RecordFormItemChildAdmin.inlines +[
        ChoiceInline,
    ]
    exclude = ['example']

class DateAdmin(RecordFormItemChildAdmin):
    base_model = Date

class RecordFormItemParentAdmin(PolymorphicParentModelAdmin):
    base_model = RecordFormItem
    polymorphic_list = True
    child_models = (
        (SingleLineText, SingleLineTextAdmin),
        (SingleLineTextWithMap, SingleLineTextWithMapAdmin),
        (MultiLineText, MultiLineTextAdmin),
        (RadioButton, RadioButtonAdmin),
        (Date, DateAdmin),
        (Checkbox, CheckboxAdmin)
    )

class QuestionInline(admin.TabularInline):
    #hack because weird ghost RecordFormItem version of this is called last
    id_cache = None
    type_cache = None
    def question_link(self, obj):
        if not self.id_cache:
            self.id_cache = obj.pk
        if self.id_cache:
            url = '<a href="%s" target="_blank">%s</a>' % (reverse_lazy("admin:wizard_builder_recordformitem_change", args=(self.id_cache,)) , obj.text)
            self.id_cache = None
            return url

    question_link.allow_tags = True

    def question_type(self, obj):
        return type(obj).__name__

    model = RecordFormItem
    sortable_field_name = "position"
    fields = ['question_link', 'question_type', 'position']
    readonly_fields = ['question_link', 'question_type']

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    extra = 0

class PageChildAdmin(PolymorphicChildModelAdmin):
    """ Base admin class for all child models """
    base_model = PageBase

class RecordFormQuestionPageAdmin(PageChildAdmin):
    base_model = RecordFormQuestionPage

    fieldsets = (
        (None, {
            'fields': ('position','section','encouragement','infobox')
        }),
        ('Advanced options', {
            'classes': ('grp-collapse grp-closed',),
            'fields': (('multiple','name_for_multiple'),)
        }),
    )

    inlines = [
        QuestionInline,
    ]

class RecordFormTextPageAdmin(PageChildAdmin):
    base_model = RecordFormTextPage

class PageParentAdmin(PolymorphicParentModelAdmin):
    """ Base admin class for all child models """
    base_model = PageBase
    polymorphic_list = True
    child_models = (
        (RecordFormQuestionPage, RecordFormQuestionPageAdmin),
        (RecordFormTextPage, RecordFormTextPageAdmin)
    )

# Only the parent needs to be registered:
admin.site.register(RecordFormItem, RecordFormItemParentAdmin)
admin.site.register(PageBase, PageParentAdmin)
admin.site.register(Conditional)

