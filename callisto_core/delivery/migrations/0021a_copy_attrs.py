# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-22 14:24
from __future__ import unicode_literals

from django.db import migrations


def _copy_attrs_for_instances(instances):
    for instance in instances:
        instance.new_sent = instance.sent
        instance.new_to_address = instance.to_address
        instance.save()


def copy_attrs(apps, schema_editor):
    current_database = schema_editor.connection.alias
    [
        _copy_attrs_for_instances(
            apps.get_model(f"delivery.{Name}").objects.using(current_database)
        )
        for Name in ["SentFullReport", "SentMatchReport"]
    ]


class Migration(migrations.Migration):

    dependencies = [("delivery", "0021_auto_20171122_1424")]

    operations = [
        migrations.RunPython(copy_attrs, reverse_code=migrations.RunPython.noop)
    ]
