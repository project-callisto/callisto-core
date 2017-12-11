# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id',
                 models.AutoField(
                     verbose_name='ID',
                     primary_key=True,
                     serialize=False,
                     auto_created=True)),
                ('is_verified',
                 models.BooleanField(
                     default=False)),
                ('school_email',
                 models.EmailField(
                     blank=True,
                     max_length=254)),
                ('user',
                 models.OneToOneField(
                     to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
