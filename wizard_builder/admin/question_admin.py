from .base import ChoiceInline, SiteAwareAdmin, SiteAwareDowncastedAdmin


class FormQuestionSiteMixin(object):

    def site_name(self, obj):
        return obj.page.site.name


class FormQuestionParentAdmin(SiteAwareDowncastedAdmin, FormQuestionSiteMixin):
    pass


class FormQuestionChildAdmin(SiteAwareAdmin, FormQuestionSiteMixin):
    pass


class MultipleChoiceParentAdmin(FormQuestionParentAdmin):
    inlines = [ChoiceInline]


class MultipleChoiceChildAdmin(FormQuestionChildAdmin):
    inlines = [ChoiceInline]
