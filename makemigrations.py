import sys
import django
from django.conf import settings

def make_migrations():
    from django.core.management import call_command
    call_command('makemigrations', 'wizard_builder')


if __name__ == '__main__':
    settings.configure(
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.sites',
            'wizard_builder',
            'wizard_builder.tests.test_app'
        ],
    )
    django.setup()
    make_migrations()
