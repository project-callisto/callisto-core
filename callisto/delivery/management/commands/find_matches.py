from django.core.management.base import BaseCommand

from callisto.delivery.matching import run_matching


class Command(BaseCommand):
    help = 'finds matches and sends match reports'

    def handle(self, *args, **options):
        # TODO: eventually: add test option that verifies that passed class can be imported & has necessary methods
        # TODO (cont): https://github.com/SexualHealthInnovations/callisto-core/issues/56
        run_matching()
        self.stdout.write('Matching run')
