# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='evalrow',
            name='action',
            field=models.CharField(choices=[('c', 'Create'), ('e', 'Edit'), ('v', 'View'), ('s', 'Submit'), ('m', 'Match'), ('mf', 'Match found'), ('w', 'Withdraw'), ('f', 'First')], max_length=2),
        ),
        migrations.AlterField(
            model_name='evalrow',
            name='user_identifier',
            field=models.CharField(max_length=500),
        ),
    ]
