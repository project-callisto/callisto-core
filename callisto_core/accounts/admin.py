from django.contrib import admin
from django.contrib.auth.models import Group, User

from .models import BulkAccount


class AccountCreationAdmin(admin.ModelAdmin):

    def changelist_view(self, *args, **kwargs):
        return super().add_view(*args, *kwargs)


admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.register(BulkAccount, AccountCreationAdmin)
