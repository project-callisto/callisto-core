import importlib

from django.core.management.base import BaseCommand

from callisto.delivery.matching import run_matching
from callisto.notification.api import NotificationApi


class Command(BaseCommand):
    help = 'finds matches and sends match reports'

    def add_arguments(self, parser):
        parser.add_argument('notifier', nargs='?', default=None)
        parser.add_argument('report_class', nargs='?', default=None)
        # eventually: add test option that verifies that passed class can be imported & has necessary methods
        # https://github.com/SexualHealthInnovations/callisto-core/issues/56

    def handle(self, *args, **options):
        if options['notifier']:
            notifier_name = options['notifier']
        else:
            notifier_name = options['report_class']
        if notifier_name:
            module_name, class_name = notifier_name.rsplit(".", 1)
            NotifierClass = getattr(importlib.import_module(module_name), class_name)
        else:
            NotifierClass = NotificationApi

        run_matching(notifier=NotifierClass)

        self.stdout.write('Matching run')
