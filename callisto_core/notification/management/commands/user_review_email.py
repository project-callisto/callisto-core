from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def send_user_review_email(self):
        pass

    def handle(self, *args, **options):
        self.send_user_review_email()
