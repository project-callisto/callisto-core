import logging

import six

from django.contrib.sites.models import Site
from django.core.mail.message import EmailMultiAlternatives
from django.db import models
from django.template import Context, Template
from django.utils.html import strip_tags

from .managers import EmailNotificationQuerySet
from .validators import validate_email_unique

logger = logging.getLogger(__name__)


@six.python_2_unicode_compatible
class EmailNotification(models.Model):
    """Record of Email constructed in and sent via the project"""
    name = models.CharField(blank=False, max_length=50)
    subject = models.CharField(blank=False, max_length=77)
    body = models.TextField(blank=False)
    sites = models.ManyToManyField(Site)
    objects = EmailNotificationQuerySet.as_manager()

    def __str__(self):
        return self.name

    def clean(self):
        self.save()
        super(EmailNotification, self).clean()
        validate_email_unique(self)

    @property
    def sitenames(self):
        return [site.name for site in self.sites.all()]

    def render_body(self, context=None):
        """Format the email as HTML."""
        if context is None:
            context = {'domain': Site.objects.get_current()}
        return Template(self.body).render(Context(context))

    def send(self, to, from_email, context=None):
        """Send the email as plain text.

        Includes an HTML equivalent version as an attachment.
        """

        if context is None:
            context = {'domain': Site.objects.get_current()}
        EmailMultiAlternatives(
            self.subject,
            self.render_body(context),
            from_email,
            to,
        ).send()
        logger.info('email_notification.send(subject={})'.format(self.subject))
