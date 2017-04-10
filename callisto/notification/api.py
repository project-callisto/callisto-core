from django.conf import settings


class EmailNotificationApi(object):

    @classmethod
    def send_match_notification(match_report):
        """Notifies reporting user that a match has been found. Requires an EmailNotification called "match_notification."

        Args:
          match_report(MatchReport): MatchReport for which a match has been found
        """
        notification = self.objects.get(name='match_notification')
        from_email = '"Callisto Matching" <notification@{0}>'.format(settings.APP_URL)
        to = match_report.contact_email
        context = {'report': match_report.report}
        notification.send(to=[to], from_email=from_email, context=context)
