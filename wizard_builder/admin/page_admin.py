from django.contrib import admin

from .base import QuestionInline


class PageAdmin(admin.ModelAdmin):
    list_filter = ['sites']
    fieldsets = (
        (None, {
            'fields': ('position', 'section', 'infobox', 'sites')
        }),
        ('Advanced options', {
            'fields': (('multiple', 'name_for_multiple'),)
        }),
    )
    inlines = [
        QuestionInline,
    ]
