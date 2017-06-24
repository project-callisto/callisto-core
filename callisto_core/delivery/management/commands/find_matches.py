from django.core.management.base import BaseCommand

from callisto.delivery.matching import MatchingApi


class Command(BaseCommand):
    help = 'finds matches and sends match reports'

    def handle(self, *args, **options):
        MatchingApi.run_matching()
        self.stdout.write('Matching run')
