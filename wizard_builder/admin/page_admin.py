from django.contrib import admin

from .base import DowncastedAdmin, QuestionInline


class PageBaseAdmin(DowncastedAdmin):
    list_filter = ['sites']


class PageBaseChildAdmin(admin.ModelAdmin):
    list_filter = ['sites']


class QuestionPageAdmin(PageBaseChildAdmin):
    fieldsets = (
        (None, {
            'fields': ('position', 'section', 'encouragement', 'infobox', 'sites')
        }),
        ('Advanced options', {
            'fields': (('multiple', 'name_for_multiple'),)
        }),
    )
    inlines = [
        QuestionInline,
    ]
