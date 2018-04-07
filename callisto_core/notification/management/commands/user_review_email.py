from django.core.management.base import BaseCommand

from callisto_core.delivery.models import MatchReport, Report
from callisto_core.utils.api import NotificationApi, TenantApi


class UserReviewCommandBackend(object):

    @property
    def site_id(self):
        return 1

    @property
    def reports(self):
        return Report.objects.filter(
            owner__account__invalid=False,
            sentfullreport__to_address__isnull=False,
        )

    @property
    def matches(self):
        return MatchReport.objects.filter(
            report__match_found=True,
            report__owner__account__invalid=False,
        )

    def send_user_review_email(self):
        NotificationApi.send_user_review_nofication(
            reports=self.reports,
            matches=self.matches,
            to_addresses=[TenantApi.site_settings('COORDINATOR_EMAIL', site_id=self.site_id)],
            public_key=TenantApi.site_settings('COORDINATOR_PUBLIC_KEY', site_id=self.site_id),
            site_id=self.site_id,
        )

    def send_user_review_slack_notification(self):
        emails = TenantApi.site_settings('COORDINATOR_EMAIL', site_id=self.site_id)
        NotificationApi.slack_notification(
            msg=f'Sent a encrypted PDF of report and match report information to {emails}',
            type='user_review',
        )


class Command(
    UserReviewCommandBackend,
    BaseCommand,
):

    def handle(self, *args, **options):
        self.send_user_review_email()
        self.send_user_review_slack_notification()
