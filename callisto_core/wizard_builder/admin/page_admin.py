from django.contrib import admin

from .inlines import QuestionInline


class PageAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('position', 'section')
        }),
    )
    inlines = [
        QuestionInline,
    ]
