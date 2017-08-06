from django import forms
from django.contrib import admin
from django.core.urlresolvers import reverse, reverse_lazy
from django.db import models
from django.utils.html import format_html

from ..models import Choice, FormQuestion


class DowncastedAdmin(admin.ModelAdmin):

    list_display = ['object_display', 'model_type']

    def get_queryset(self, request):
        base_queryset = super(DowncastedAdmin, self).get_queryset(request)
        return base_queryset.select_subclasses()

    def object_display(self, obj):
        model_name = obj.__class__.__name__
        reverse_url = 'admin:{}_{}_change'.format(
            obj._meta.app_label,
            model_name.lower(),
        )
        url = reverse(reverse_url, args=(obj.id,))
        text = obj.__str__()
        return format_html('<a href="{}">{}</a>'.format(url, text))
    object_display.short_description = 'Object'

    def model_type(self, obj):
        model_name = obj.__class__.__name__
        reverse_url = 'admin:{}_{}_changelist'.format(
            obj._meta.app_label,
            model_name.lower(),
        )
        url = reverse(reverse_url)
        text = obj.__class__._meta.verbose_name.capitalize()
        return format_html('<a href="{}">{}</a>'.format(url, text))
    model_type.short_description = 'Type'


class ChoiceInline(admin.TabularInline):
    fields = ['text', 'position', 'extra_info_placeholder', 'id']
    model = Choice
    sortable_field_name = "position"
    extra = 0
    readonly_fields = ('id',)
    formfield_overrides = {
        models.TextField: {'widget': forms.TextInput},
    }


class QuestionInline(admin.TabularInline):
    # hack because weird ghost FormQuestion version of this is called last
    id_cache = None
    type_cache = None

    def question_link(self, obj):
        if not self.id_cache:
            self.id_cache = obj.pk
        if self.id_cache:
            url = '<a href="%s" target="_blank">%s</a>' % (reverse_lazy(
                "admin:wizard_builder_formquestion_change", args=(self.id_cache,)), obj.text)
            self.id_cache = None
            return url

    question_link.allow_tags = True

    def question_type(self, obj):
        return type(obj).__name__

    model = FormQuestion
    sortable_field_name = "position"
    fields = ['question_link', 'question_type', 'position']
    readonly_fields = ['question_link', 'question_type']

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    extra = 0
