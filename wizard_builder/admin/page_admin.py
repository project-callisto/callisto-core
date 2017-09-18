from django.contrib import admin

from .base import QuestionInline


class PageAdmin(admin.ModelAdmin):
    list_filter = ['sites']
    fieldsets = (
        (None, {
            'fields': ('position', 'section', 'sites')
        }),
    )
    inlines = [
        QuestionInline,
    ]
