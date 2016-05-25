# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wizard_builder', '0001_initial'),
        ('evaluation', '0006_auto_20151211_1846'),
    ]

    operations = [
        migrations.CreateModel(
            name='EvaluationField',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('label', models.CharField(max_length=500)),
                ('question', models.OneToOneField(to='wizard_builder.FormQuestion')),
            ],
        ),
    ]
