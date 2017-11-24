from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'create a demo user'

    def create_demo_user(self):
        User.objects.create_user(
            username='demo',
            password='demo',
        )

    def handle(self, *args, **options):
        self.create_demo_user()
