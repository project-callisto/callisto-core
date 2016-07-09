from django.contrib import admin

from .models import EmailNotification


class EmailNotificationAdmin(admin.ModelAdmin):

    class Media:
        js = [
            '/static/grappelli/tinymce/jscripts/tiny_mce/tiny_mce.js',
            '/static/js/tinymce_setup.js',
        ]


admin.site.register(EmailNotification, EmailNotificationAdmin)
