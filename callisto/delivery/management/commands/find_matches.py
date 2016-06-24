from callisto.delivery.matching import find_matches
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help='finds matches and sends match reports'

    def handle(self, *args, **options):
        find_matches()
        self.stdout.write('Matching run')
