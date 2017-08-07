# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-12 20:48
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wizard_builder', '0004_inheritence_downcasting'),
    ]

    operations = [
        migrations.AlterField(
            model_name='conditional',
            name='page',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.PROTECT,
                to='wizard_builder.PageBase'),
        ),
        migrations.AlterField(
            model_name='conditional',
            name='question',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to='wizard_builder.FormQuestion'),
        ),
        migrations.AlterField(
            model_name='formquestion',
            name='page',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='wizard_builder.QuestionPage'),
        ),
    ]
