from django.contrib import admin
from django.db import models
from django.forms import CheckboxSelectMultiple

from .models import EmailNotification


class EmailNotificationAdmin(admin.ModelAdmin):

    # UX change, doesn't change functionality any
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }

    list_display = ['name', 'sitenames']
    search_fields = ['url', 'title']
    list_filter = ['sites']


admin.site.register(EmailNotification, EmailNotificationAdmin)
