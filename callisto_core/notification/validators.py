from django.core.exceptions import ValidationError


def validate_email_unique(email):
    EmailNotification = email.__class__
    invalid_sites = []
    for site in email.sites.all():
        if EmailNotification.objects.filter(
            name=email.name, sites__id__in=[
                site.id]).exclude(
                id=email.id):
            invalid_sites.append(site.domain)
            email.sites.remove(site.id)
    if invalid_sites:
        raise ValidationError('''
                EmailNotification already exists with (name={}, sites__domain__in=[{}])
            '''.format(email.name, invalid_sites))
