import json

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.test import TestCase

from ...delivery.models import MatchReport, Report
from ...delivery.report_delivery import MatchReportContent

User = get_user_model()


class MatchSetup(TestCase):

    def setUp(self):
        self.site = Site.objects.get(id=1)
        self.site.domain = 'testserver'
        self.site.save()
        self.user1 = User.objects.create_user(
            username="test", password="test",
        )
        self.user2 = User.objects.create_user(
            username="tset", password="test",
        )

    def create_match(self, user, identifier, match_report_content=None):
        report = Report(owner=user)
        report.encrypt_report("test report 1", "key")
        match_report = MatchReport(report=report, identifier=identifier)

        if match_report_content:
            match_report_object = match_report_content
        else:
            match_report_object = MatchReportContent(
                identifier='test', perp_name='test',
                email='test@example.com', phone="test",
            )

        match_report.encrypt_match_report(
            json.dumps(match_report_object.__dict__),
            identifier,
        )

        return match_report
