from django.contrib.sites.models import Site
from django.db import models

from .managers import EmailNotificationQuerySet
from .validators import validate_email_unique


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
