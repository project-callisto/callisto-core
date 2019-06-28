from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "create a demo user"

    def create_demo_user(self):
        User.objects.create_user(username="demo", password="demo")

    def handle(self, *args, **options):
        self.create_demo_user()
