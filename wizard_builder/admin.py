from django import forms
from django.contrib import admin
from django.core.urlresolvers import reverse_lazy
from django.db import models
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Checkbox, Choice, Conditional, Date, FormQuestion, MultiLineText, PageBase,
    QuestionPage, RadioButton, SingleLineText, SingleLineTextWithMap, TextPage,
)


class DowncastedAdmin(admin.ModelAdmin):

    list_display = ['object_display', 'model_type']

    def get_queryset(self, request):
        base_queryset = super(DowncastedAdmin, self).get_queryset(request)
        return base_queryset.select_subclasses()

    def object_display(self, obj):
        model_name = obj.__class__.__name__
        reverse_url = 'admin:{}_{}_change'.format(
            obj._meta.app_label,
            model_name.lower(),
        )
        url = reverse(reverse_url, args=(obj.id,))
        text = obj.__str__()
        return format_html('<a href="{}">{}</a>'.format(url, text))
    object_display.short_description = 'Object'

    def model_type(self, obj):
        model_name = obj.__class__.__name__
        reverse_url = 'admin:{}_{}_changelist'.format(
            obj._meta.app_label,
            model_name.lower(),
        )
        url = reverse(reverse_url)
        text = model_name
        return format_html('<a href="{}">{}</a>'.format(url, text))
    model_type.short_description = 'Type'


class SingleLineTextAdmin(DowncastedAdmin):
    base_model = SingleLineText


class MultiLineTextAdmin(DowncastedAdmin):
    base_model = MultiLineText


class SingleLineTextWithMapAdmin(DowncastedAdmin):
    base_model = MultiLineText


class ChoiceInline(admin.TabularInline):
    fields = ['text', 'position', 'extra_info_placeholder', 'id']
    model = Choice
    sortable_field_name = "position"
    extra = 0
    readonly_fields = ('id',)
    formfield_overrides = {
        models.TextField: {'widget': forms.TextInput},
    }


class RadioButtonAdmin(DowncastedAdmin):
    base_model = RadioButton
    inlines = [
        ChoiceInline,
    ]


class CheckboxAdmin(DowncastedAdmin):
    base_model = Checkbox
    inlines = [
        ChoiceInline,
    ]


class DateAdmin(DowncastedAdmin):
    base_model = Date


class FormQuestionParentAdmin(DowncastedAdmin):
    base_model = FormQuestion
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


class QuestionPageAdmin(admin.ModelAdmin):
    base_model = QuestionPage

    fieldsets = (
        (None, {
            'fields': ('position', 'section', 'encouragement', 'infobox', 'site')
        }),
        ('Advanced options', {
            'fields': (('multiple', 'name_for_multiple'),)
        }),
    )

    inlines = [
        QuestionInline,
    ]


class TextPageAdmin(admin.ModelAdmin):
    pass


class PageBaseAdmin(DowncastedAdmin):
    list_display = DowncastedAdmin.list_display + [
        'site_name',
    ]

    def site_name(self, obj):
        return obj.site.name


# Only the parent needs to be registered:
admin.site.register(FormQuestion, FormQuestionParentAdmin)

admin.site.register(PageBase, PageBaseAdmin)
admin.site.register(QuestionPage, QuestionPageAdmin)
admin.site.register(TextPage, TextPageAdmin)

admin.site.register(Conditional)
