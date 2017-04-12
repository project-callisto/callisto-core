from django.conf import settings

from callisto.notification.models import EmailNotification


class NotificationApi(object):

    model = EmailNotification
    from_email = '"Reports" <reports@{0}>'.format(settings.APP_URL)

    @classmethod
    def send_match_notification(cls, user, match_report):
        """Notifies reporting user that a match has been found. Requires an EmailNotification called "match_notification."

        Args:
          user(User): reporting user
          match_report(MatchReport): MatchReport for which a match has been found
        """
        notification = cls.model.objects.on_site().get(name='match_notification')
        from_email = '"Callisto Matching" <notification@{0}>'.format(settings.APP_URL)
        to = match_report.contact_email
        context = {'report': match_report.report}
        notification.send(to=[to], from_email=from_email, context=context)
