import logging

from django.conf import settings

from .models import EmailNotification, MatchReport
from .report_delivery import PDFMatchReport

logger = logging.getLogger(__name__)


def find_matches(identifiers=None, report_class=PDFMatchReport):
    logger.info("running matching")
    if identifiers is None:
        identifiers = [match_report.identifier for match_report in MatchReport.objects.filter(seen=False)]
    run_matching(identifiers, report_class=report_class)


def run_matching(identifiers, report_class=PDFMatchReport):
    for identifier in identifiers:
        match_list = [potential for potential in MatchReport.objects.all() if potential.get_match(identifier)]
        if len(match_list) > 1:
            seen_match_owners = [match.report.owner for match in match_list if match.seen]
            new_match_owners = [match.report.owner for match in match_list if not match.seen]
            # filter out multiple reports made by the same person
            if len(set(seen_match_owners + new_match_owners)) > 1:
                # only send notifications if new matches are submitted by owners we don't know about
                if not set(new_match_owners).issubset(set(seen_match_owners)):
                    process_new_matches(match_list, identifier, report_class)
                for match_report in match_list:
                    match_report.report.match_found = True
                    match_report.report.save()
        for match in match_list:
            match.seen = True
            # delete identifier, which should only be filled for newly added match reports in delayed matching case
            match.identifier = None
            match.save()


def process_new_matches(matches, identifier, report_class):
    logger.info("new match found")
    owners_notified = []
    for match_report in matches:
        owner = match_report.report.owner
        #only send notification emails to new matches
        if owner not in owners_notified and not match_report.report.match_found and not match_report.report.submitted_to_school:
            send_notification_email(owner, match_report)
            owners_notified.append(owner)
    #send report to school
    report_class(matches, identifier).send_matching_report_to_school()

def send_notification_email(user, match_report):
    notification = EmailNotification.objects.get(name='match_notification')
    from_email = '"Callisto Matching" <notification@{0}>'.format(settings.APP_URL)
    to = match_report.contact_email
    context = {'report': match_report.report}
    notification.send(to=[to], from_email=from_email, context=context)
