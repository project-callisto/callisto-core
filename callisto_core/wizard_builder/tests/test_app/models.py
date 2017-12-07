from django.db import models


class Report(models.Model):

    text = models.TextField(blank=False, null=False)
