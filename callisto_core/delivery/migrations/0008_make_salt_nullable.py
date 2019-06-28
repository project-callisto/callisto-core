# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("delivery", "0007_add_argon2_with_rolling_upgrades")]

    operations = [
        migrations.AlterField(
            model_name="matchreport",
            name="salt",
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name="report",
            name="salt",
            field=models.CharField(max_length=256, null=True),
        ),
    ]
