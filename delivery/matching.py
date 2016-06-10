from django.conf import settings

from .models import EmailNotification, MatchReport
from .report_delivery import send_matching_report_to_school


def find_matches():
    new_identifiers = MatchReport.objects.filter(seen=False).order_by('identifier').distinct('identifier')
    for row in new_identifiers.values():
        matches = MatchReport.objects.filter(identifier=row['identifier'])
        match_list = list(matches)
        if len(match_list) > 1 :
            seen_match_owners = [match.report.owner for match in match_list if match.seen]
            new_match_owners = [match.report.owner for match in match_list if not match.seen]
            all_owners = seen_match_owners + new_match_owners
            # filter out reports made by the same person
            if len(set(all_owners)) > 1:
                # only send notifications if new owners are actually new
                if not set(new_match_owners).issubset(set(seen_match_owners)):
                    process_new_matches(match_list)
                #new owners all already have existing matches
                for match_report in match_list:
                    match_report.report.match_found = True
                    match_report.report.save()
        matches.update(seen=True)

def process_new_matches(matches):
    owners_notified = []
    for match_report in matches:
        owner = match_report.report.owner
        #only send notification emails to new matches
        if owner not in owners_notified and not match_report.report.match_found and not match_report.report.submitted_to_school:
            send_notification_email(owner, match_report)
            owners_notified.append(owner)
    #send report to school
    send_matching_report_to_school(matches)


def send_notification_email(user, match_report):
    notification = EmailNotification.objects.get(name='match_notification')
    from_email = '"Callisto Matching" <notification@{0}>'.format(settings.APP_URL)
    to = set([user.account.school_email, match_report.contact_email])
    context = {'report': match_report.report}
    notification.send(to=to, from_email=from_email, context=context)
