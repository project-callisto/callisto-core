from django.contrib import admin

from .base import QuestionInline, DowncastedAdmin


class PageBaseAdmin(DowncastedAdmin):
    list_display = DowncastedAdmin.list_display + ['site_name']
    list_filter = ['site']

    def site_name(self, obj):
        return obj.site.name


class PageBaseChildAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'site_name']
    list_filter = ['site']

    def site_name(self, obj):
        return obj.site.name


class QuestionPageAdmin(PageBaseChildAdmin):
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
