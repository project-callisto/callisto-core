from django.core.exceptions import ValidationError


def validate_email_unique(email):
    EmailNotification = email.__class__
    for site in email.sites.all():
        if EmailNotification.objects.filter(name=email.name, sites__id__in=[site.id]).exclude(id=email.id):
            email.delete()
            raise ValidationError('''
                    EmailNotification already exists with (name={} ,site__domain={})
                '''.format(email.name, site.domain))
