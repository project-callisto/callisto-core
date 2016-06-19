# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailNotification',
            fields=[
                ('name', models.CharField(primary_key=True, max_length=50, serialize=False)),
                ('subject', models.CharField(max_length=77)),
                ('body', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='MatchReport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('contact_phone', models.CharField(max_length=256)),
                ('contact_voicemail', models.TextField(null=True, blank=True)),
                ('contact_name', models.TextField(null=True, blank=True)),
                ('contact_email', models.EmailField(max_length=256)),
                ('contact_notes', models.TextField(null=True, blank=True)),
                ('identifier', models.CharField(max_length=500)),
                ('name', models.CharField(null=True, max_length=500, blank=True)),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('seen', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('encrypted', models.BinaryField()),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('last_edited', models.DateTimeField(null=True, blank=True)),
                ('salt', models.CharField(max_length=256)),
                ('submitted_to_school', models.DateTimeField(null=True, blank=True)),
                ('contact_phone', models.CharField(null=True, max_length=256, blank=True)),
                ('contact_voicemail', models.TextField(null=True, blank=True)),
                ('contact_email', models.EmailField(null=True, max_length=256, blank=True)),
                ('contact_notes', models.TextField(null=True, blank=True)),
                ('contact_name', models.TextField(null=True, blank=True)),
                ('match_found', models.BooleanField(default=False)),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-added',),
            },
        ),
        migrations.CreateModel(
            name='SentReport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('sent', models.DateTimeField(auto_now_add=True)),
                ('to_address', models.EmailField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SentFullReport',
            fields=[
                ('sentreport_ptr', models.OneToOneField(to='delivery.SentReport', primary_key=True, auto_created=True, serialize=False, parent_link=True)),
                ('report', models.ForeignKey(to='delivery.Report', blank=True, on_delete=django.db.models.deletion.SET_NULL, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('delivery.sentreport',),
        ),
        migrations.CreateModel(
            name='SentMatchReport',
            fields=[
                ('sentreport_ptr', models.OneToOneField(to='delivery.SentReport', primary_key=True, auto_created=True, serialize=False, parent_link=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('delivery.sentreport',),
        ),
        migrations.AddField(
            model_name='sentreport',
            name='polymorphic_ctype',
            field=models.ForeignKey(to='contenttypes.ContentType', null=True, related_name='polymorphic_delivery.sentreport_set+', editable=False),
        ),
        migrations.AddField(
            model_name='matchreport',
            name='report',
            field=models.ForeignKey(to='delivery.Report'),
        ),
        migrations.AddField(
            model_name='sentmatchreport',
            name='reports',
            field=models.ManyToManyField(to='delivery.MatchReport'),
        ),
    ]
