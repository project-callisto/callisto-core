import os

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):

    def handle(self, *args, **options):
        username = os.environ.get('ADMIN_USER', 'user')
        password = os.environ.get('ADMIN_PASS', 'pass')
        if not User.objects.filter(username=username):
            User.objects.create_superuser(username, '', password)
