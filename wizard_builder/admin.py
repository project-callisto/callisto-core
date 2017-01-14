# TODO: remove grappelli dependency
from grappelli.forms import GrappelliSortableHiddenMixin
from polymorphic.admin import (
    PolymorphicChildModelAdmin, PolymorphicParentModelAdmin,
)

from django import forms
from django.contrib import admin
from django.core.urlresolvers import reverse_lazy
from django.db import models

from .models import (
    Checkbox, Choice, Conditional, Date, FormQuestion, MultiLineText, PageBase,
    QuestionPage, RadioButton, SingleLineText, SingleLineTextWithMap, TextPage,
)


class FormQuestionChildAdmin(PolymorphicChildModelAdmin):
    """ Base admin class for all child models """
    base_model = FormQuestion


class SingleLineTextAdmin(FormQuestionChildAdmin):
    base_model = SingleLineText


class MultiLineTextAdmin(FormQuestionChildAdmin):
    base_model = MultiLineText


class SingleLineTextWithMapAdmin(FormQuestionChildAdmin):
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


class RadioButtonAdmin(FormQuestionChildAdmin):
    base_model = RadioButton
    inlines = FormQuestionChildAdmin.inlines + [
        ChoiceInline,
    ]


class CheckboxAdmin(FormQuestionChildAdmin):
    base_model = Checkbox
    inlines = FormQuestionChildAdmin.inlines + [
        ChoiceInline,
    ]


class DateAdmin(FormQuestionChildAdmin):
    base_model = Date


class FormQuestionParentAdmin(PolymorphicParentModelAdmin):
    base_model = FormQuestion
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
    # hack because weird ghost FormQuestion version of this is called last
    id_cache = None
    type_cache = None

    def question_link(self, obj):
        if not self.id_cache:
            self.id_cache = obj.pk
        if self.id_cache:
            url = '<a href="%s" target="_blank">%s</a>' % (reverse_lazy("admin:wizard_builder_formquestion_change",
                                                                        args=(self.id_cache,)), obj.text)
            self.id_cache = None
            return url

    question_link.allow_tags = True

    def question_type(self, obj):
        return type(obj).__name__

    model = FormQuestion
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


class QuestionPageAdmin(PageChildAdmin):
    base_model = QuestionPage

    fieldsets = (
        (None, {
            'fields': ('position', 'section', 'encouragement', 'infobox')
        }),
        ('Advanced options', {
            'classes': ('grp-collapse grp-closed',),
            'fields': (('multiple', 'name_for_multiple'),)
        }),
    )

    inlines = [
        QuestionInline,
    ]


class TextPageAdmin(PageChildAdmin):
    base_model = TextPage


class PageParentAdmin(PolymorphicParentModelAdmin):
    """ Base admin class for all child models """
    base_model = PageBase
    polymorphic_list = True
    child_models = (
        (QuestionPage, QuestionPageAdmin),
        (TextPage, TextPageAdmin)
    )


# Only the parent needs to be registered:
admin.site.register(FormQuestion, FormQuestionParentAdmin)
admin.site.register(PageBase, PageParentAdmin)
admin.site.register(Conditional)
