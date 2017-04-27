from django.core.exceptions import ValidationError


def validate_email_unique(email):
    EmailNotification = email.__class__
    for site in email.sites.all():
        if EmailNotification.objects.filter(name=email.name, sites__id__in=[site.id]).exclude(id=email.id):
            raise ValidationError('EmailNotification already exists with (name={},site_id={})'.format(email.name, site.id))
