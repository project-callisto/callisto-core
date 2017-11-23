import nested_admin

from django import forms
from django.contrib import admin
from django.core.urlresolvers import reverse_lazy
from django.db import models

from ..models import Choice, ChoiceOption, FormQuestion


class ChoiceOptionInline(nested_admin.NestedStackedInline):
    extra = 0
    model = ChoiceOption
    formfield_overrides = {
        models.TextField: {'widget': forms.TextInput},
    }


class ChoiceInline(nested_admin.NestedStackedInline):
    model = Choice
    sortable_field_name = "position"
    extra = 0
    formfield_overrides = {
        models.TextField: {'widget': forms.TextInput},
    }
    inlines = [
        ChoiceOptionInline,
    ]


class QuestionInline(admin.TabularInline):
    # hack because weird ghost FormQuestion version of this is called last
    id_cache = None
    type_cache = None
    extra = 0

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
