from django.contrib import admin

from .base import ChoiceInline, DowncastedAdmin


class FormQuestionParentAdmin(DowncastedAdmin):
    list_display = DowncastedAdmin.list_display + ['site_name']

    def site_name(self, obj):
        return obj.page.site.name


class FormQuestionChildAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'site_name']

    def site_name(self, obj):
        return obj.page.site.name


class MultipleChoiceParentAdmin(FormQuestionParentAdmin):
    inlines = [ChoiceInline]


class MultipleChoiceChildAdmin(FormQuestionChildAdmin):
    inlines = [ChoiceInline]
