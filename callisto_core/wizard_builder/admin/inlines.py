import nested_admin

from django import forms
from django.contrib import admin
from django.db import models
from django.urls import reverse_lazy

from callisto_core.wizard_builder.models import Choice, ChoiceOption, FormQuestion


class ChoiceOptionInline(nested_admin.NestedStackedInline):
    extra = 0
    model = ChoiceOption
    formfield_overrides = {
        models.TextField: {'widget': forms.TextInput},
    }


class ChoiceInline(nested_admin.NestedStackedInline):
    model = Choice
    extra = 0
    formfield_overrides = {
        models.TextField: {'widget': forms.TextInput},
    }
    inlines = [
        ChoiceOptionInline,
    ]
    fields = ['text', 'position', 'extra_info_text']


class QuestionInline(admin.TabularInline):
    id_cache = None
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

    model = FormQuestion
    fields = ['question_link', 'type', 'position']
    readonly_fields = ['question_link', 'type']
