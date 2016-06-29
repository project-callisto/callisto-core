import hashlib

import nacl.secret
import nacl.utils
import six
from polymorphic.models import PolymorphicModel

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail.message import EmailMultiAlternatives
from django.db import models
from django.template import Context, Template
from django.utils import timezone
from django.utils.crypto import get_random_string, pbkdf2
from django.utils.html import strip_tags


class Report(models.Model):
    encrypted = models.BinaryField(blank=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL)
    added = models.DateTimeField(auto_now_add=True)
    last_edited = models.DateTimeField(blank=True, null=True)
    salt = models.CharField(blank=False, max_length=256)

    submitted_to_school = models.DateTimeField(blank=True, null=True)
    contact_phone = models.CharField(blank=True, null=True, max_length=256)
    contact_voicemail = models.TextField(blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True, max_length=256)
    contact_notes = models.TextField(blank=True, null=True)
    contact_name = models.TextField(blank=True, null=True)

    @property
    def entered_into_matching(self):
        first_match_report = self.matchreport_set.first()
        if first_match_report:
            return first_match_report.added
        else:
            return None

    match_found = models.BooleanField(default=False)

    class Meta:
        ordering = ('-added',)

    def encrypt_report(self, report_text, key):
        if not self.salt:
            self.salt = get_random_string()
        else:
            self.last_edited = timezone.now()
        stretched_key = pbkdf2(key, self.salt, settings.KEY_ITERATIONS, digest=hashlib.sha256)
        box = nacl.secret.SecretBox(stretched_key)
        message = report_text.encode('utf-8')
        nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
        encrypted = box.encrypt(message, nonce)
        self.encrypted = encrypted

    def decrypted_report(self, key):
        stretched_key = pbkdf2(key, self.salt, settings.KEY_ITERATIONS, digest=hashlib.sha256)
        box = nacl.secret.SecretBox(stretched_key)
        decrypted = box.decrypt(bytes(self.encrypted))
        return decrypted.decode('utf-8')

    def withdraw_from_matching(self):
        self.matchreport_set.all().delete()
        self.match_found = False

    @property
    def get_submitted_report_id(self):
        if self.submitted_to_school:
            sent_report = self.sentfullreport_set.first()
            report_id = sent_report.get_report_id() if sent_report else None
            return report_id
        else:
            return None

@six.python_2_unicode_compatible
class EmailNotification(models.Model):
    name = models.CharField(blank=False, max_length=50, primary_key=True)
    subject = models.CharField(blank=False, max_length=77)
    body = models.TextField(blank=False)

    def __str__(self):
        return self.name

    def render_body(self, context={}):
        current_site = Site.objects.get_current()
        context['domain'] = current_site.domain
        return Template(self.body).render(Context(context))

    def render_body_plain(self, context={}):
        html = self.render_body(context)
        cleaned = html.replace('<br />','\n')
        cleaned = cleaned.replace('<br/>','\n')
        cleaned = cleaned.replace('<p>','\n')
        cleaned = cleaned.replace('</p>', '\n')
        return strip_tags(cleaned)

    def send(self, to, from_email, context={}):
        email = EmailMultiAlternatives(self.subject, self.render_body_plain(context), from_email, to)
        email.attach_alternative(self.render_body(context), "text/html")
        email.send()

@six.python_2_unicode_compatible
class MatchReport(models.Model):
    report = models.ForeignKey('Report')
    contact_phone = models.CharField(blank=False, max_length=256)
    contact_voicemail = models.TextField(blank=True, null=True)
    contact_name = models.TextField(blank=True, null=True)
    contact_email = models.EmailField(blank=False, max_length=256)
    contact_notes = models.TextField(blank=True, null=True)

    identifier = models.CharField(blank=False, max_length=500)
    name = models.CharField(blank=True, null=True, max_length=500)

    added = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(blank=False, default=False)

    def __str__(self):
        return "Match report for report {0}".format(self.report.pk)

class SentReport(PolymorphicModel):
    # TODO: store link to s3 backup https://github.com/SexualHealthInnovations/callisto-core/issues/14
    sent = models.DateTimeField(auto_now_add=True)
    to_address = models.EmailField(blank=False, null=False, max_length=256)

    def _get_id_for_schools(self, is_match):
        return "{0}-{1}-{2}".format(settings.SCHOOL_REPORT_PREFIX, '%05d' % self.id, 0 if is_match else 1)

class SentFullReport(SentReport):
    report = models.ForeignKey(Report, blank=True, null=True, on_delete=models.SET_NULL)

    def get_report_id(self):
        return self._get_id_for_schools(is_match=False)

class SentMatchReport(SentReport):
    reports = models.ManyToManyField(MatchReport)

    def get_report_id(self):
        return self._get_id_for_schools(is_match=True)
