from __future__ import unicode_literals

from django.db import migrations, models


def move_sites(apps, schema_editor):
    current_database = schema_editor.connection.alias
    Page = apps.get_model('wizard_builder.Page')
    for page in Page.objects.using(current_database):
        sites = page.sites.all()
        for question in page.formquestion_set.all():
            question.sites.add(*sites)


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0002_alter_domain_unique'),
        ('wizard_builder', '0048_formquestion_sites'),
    ]

    operations = [
        migrations.RunPython(
            move_sites,
            migrations.RunPython.noop,
        ),
    ]
