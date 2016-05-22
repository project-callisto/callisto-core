# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wizard_builder', '0001_initial'),
        ('evaluation', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EvalField',
            fields=[
                ('question', models.OneToOneField(to='wizard_builder.FormQuestion', serialize=False, primary_key=True)),
            ],
        ),
        migrations.AlterField(
            model_name='evalrow',
            name='action',
            field=models.CharField(choices=[('e', 'Edit'), ('c', 'Create'), ('s', 'Submit'), ('v', 'View')], max_length=2),
        ),
    ]
