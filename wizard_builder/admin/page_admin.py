from django.contrib import admin

from .base import DowncastedAdmin, QuestionInline


class PageBaseAdmin(DowncastedAdmin):
    list_filter = ['site']


class PageBaseChildAdmin(admin.ModelAdmin):
    list_filter = ['site']


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
