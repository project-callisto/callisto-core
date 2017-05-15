from .base import QuestionInline, SiteAwareAdmin, SiteAwareDowncastedAdmin


class PageBaseSiteMixin(object):

    def site_name(self, obj):
        return obj.site.name


class PageBaseChildAdmin(SiteAwareAdmin, PageBaseSiteMixin):
    pass


class PageBaseAdmin(SiteAwareDowncastedAdmin, PageBaseSiteMixin):
    pass


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
