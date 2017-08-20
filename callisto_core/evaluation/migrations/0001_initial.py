# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wizard_builder', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EvalRow',
            fields=[('id', models.AutoField(
                verbose_name='ID', auto_created=True,
                primary_key=True, serialize=False)),
                ('record_identifier', models.CharField(
                    max_length=500)),
                ('action', models.CharField(
                    choices=[('c', 'Create'),
                             ('e', 'Edit'),
                             ('v', 'View'),
                             ('s', 'Submit'),
                             ('m', 'Match'),
                             ('w', 'Withdraw'),
                             ('f', 'First')],
                    max_length=2)),
                ('row', models.BinaryField(blank=True)),
                ('timestamp', models.DateTimeField(
                    auto_now_add=True)),
                ('user_identifier', models.CharField(
                    max_length=500, default='default')), ],),
        migrations.CreateModel(
            name='EvaluationField',
            fields=[('id', models.AutoField(
                verbose_name='ID', auto_created=True,
                primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=500)),
                ('question', models.OneToOneField(
                    to='wizard_builder.FormQuestion')), ],), ]
