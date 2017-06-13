from django.contrib import admin

from .base import ChoiceInline, DowncastedAdmin


class FormQuestionAdminMixin(object):
    search_fields = ['text', 'descriptive_text']
    list_filter = ['page__sites']


class FormQuestionParentAdmin(FormQuestionAdminMixin, DowncastedAdmin):
    list_display = ['short_str', 'model_type', 'page']


class FormQuestionChildAdmin(FormQuestionAdminMixin, admin.ModelAdmin):
    list_display = ['short_str', 'page']


class MultipleChoiceParentAdmin(FormQuestionParentAdmin):
    inlines = [ChoiceInline]


class MultipleChoiceChildAdmin(FormQuestionChildAdmin):
    inlines = [ChoiceInline]
