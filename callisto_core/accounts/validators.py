import logging

from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe

logger = logging.getLogger(__name__)


def validate_school_email(email, school_email_domain):
    if not school_email_domain:  # demo sites use empty school email domains
        return True

    input_email_domain = email.rsplit("@", 1)[-1].lower()
    allowed = [
        _domain.strip().strip("@").strip() for _domain in school_email_domain.split(",")
    ]

    if input_email_domain not in allowed and not settings.DEBUG:
        # XXX (lojikil//Stefan Trail of Bits): I just want to raise if we're ok with this
        # since if a user adds a specific domain that can easily be tied back to them
        # (say, me@lojikil.com, lojikil.com would be logged here), someone with access to
        # the logs could tie a report back to a user. Not concerning per se, but something
        # we should be aware of
        logger.warning(
            f"non school email {input_email_domain} used for domain {school_email_domain}"
        )
        raise forms.ValidationError(
            mark_safe(
                f"Please enter a student email that matches {school_email_domain}. \
            If you're getting this message and you think you shouldn't be, \
            contact us at support@projectcallisto.org."
            )
        )
