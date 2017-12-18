import logging

from config.env import site_settings

from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe

logger = logging.getLogger(__name__)


def non_school_email_error(request=None, site_id=None):
    return mark_safe('''
        Please enter a valid {} student email.
        If you're getting this message and you think you shouldn't be,
        contact us at support@projectcallisto.org.
    '''.format(
        site_settings('SCHOOL_SHORTNAME', request=request, site_id=site_id),
    ))


def validate_school_email(email, request=None, site_id=None):
    email_domain = email.rsplit('@', 1)[-1].lower()
    school_email_domain = site_settings(
        'SCHOOL_EMAIL_DOMAIN',
        request=request,
        site_id=site_id,
    )

    allowed = [
        _domain.strip().strip('@').strip()
        for _domain in school_email_domain.split(',')
    ]
    allowed.append('sexualhealthinnovations.org')
    allowed.append('projectcallisto.org')

    if email_domain not in allowed and not settings.DEBUG:
        logger.warning(
            "non school email used with domain {}".format(email_domain))
        raise forms.ValidationError(non_school_email_error(
            request=request,
            site_id=site_id,
        ))
