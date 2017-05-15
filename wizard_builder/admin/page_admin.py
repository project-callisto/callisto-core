from .base import QuestionInline, DowncastedAdmin


class PageBaseChildAdmin(DowncastedAdmin):
    list_display = ['__str__', 'site_name']
    list_filter = ['site']

    def site_name(self, obj):
        return obj.site.name


class PageBaseParentAdmin(PageBaseChildAdmin):
    list_display = DowncastedAdmin.list_display + [
        'site_name',
    ]


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


class TextPageAdmin(PageBaseChildAdmin):
    pass


class PageBaseAdmin(PageBaseParentAdmin):
    pass
