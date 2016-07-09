import logging

from django.conf import settings

from callisto.evaluation.models import EvalRow

from .models import EmailNotification, MatchReport
from .report_delivery import PDFMatchReport

logger = logging.getLogger(__name__)


def run_matching(identifiers=None, report_class=PDFMatchReport):
    """Compares existing match records to see if any match the given identifiers. If no identifiers are given, checks
    existing match records against identifiers from records that weren't been marked as "seen" the last time matching
    was run. For each identifier for which a new match is found, a report is sent to the receiving authority and the
    reporting users are notified.

    Args:
      identifiers(list of strings, optional): the new identifiers to check for matches, or None if the value is to be
        queried from the DB (Default value = None)
      report_class(report generator class, optional): Must have `send_matching_report_to_school` method. (Default
      value = PDFMatchReport)
    """
    logger.info("running matching")
    if identifiers is None:
        identifiers = [match_report.identifier for match_report in MatchReport.objects.filter(seen=False)]
    find_matches(identifiers, report_class=report_class)


def find_matches(identifiers, report_class=PDFMatchReport):
    """Finds sets of matching records that haven't been identified yet. For a match to count as new, there must be
    associated Reports from at least 2 different users and at least one MatchReport must be newly created since we last
    checked for matches.

    Args:
      identifiers (list of str): the new identifiers to check for matches
      report_class(report generator class, optional): Must have `send_matching_report_to_school` method. (Default
      value = PDFMatchReport)
    """
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
    """Sends a report to the receiving authority and notifies the reporting users. Each user should only be notified
    one time when a match is found.

    Args:
      matches (list of MatchReports): the MatchReports that correspond to this identifier
      identifier (str): identifier associated with the MatchReports
      report_class(report generator class, optional): Must have `send_matching_report_to_school` method. (Default
      value = PDFMatchReport)
    """
    logger.info("new match found")
    owners_notified = []
    for match_report in matches:
        EvalRow.store_eval_row(action=EvalRow.MATCH_FOUND, report=match_report.report)
        owner = match_report.report.owner
        # only send notification emails to new matches
        if owner not in owners_notified and not match_report.report.match_found and not match_report.report.submitted_to_school:
            send_notification_email(owner, match_report)
            owners_notified.append(owner)
    # send report to school
    report_class(matches, identifier).send_matching_report_to_school()

def send_notification_email(user, match_report):
    """Notifies reporting user that a match has been found. Requires an EmailNotification called "match_notification."

    Args:
      user(User): reporting user
      match_report(MatchReport): MatchReport for which a match has been found
    """
    notification = EmailNotification.objects.get(name='match_notification')
    from_email = '"Callisto Matching" <notification@{0}>'.format(settings.APP_URL)
    to = match_report.contact_email
    context = {'report': match_report.report}
    notification.send(to=[to], from_email=from_email, context=context)
