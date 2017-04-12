
def make_migrations():
    from django.core.management import call_command
    call_command('makemigrations', 'test_app')
    call_command('makemigrations', 'wizard_builder')


if __name__ == '__main__':
    import sys
    sys.path.append('./src/')

    try:
        from django.conf import settings

        settings.configure(
            INSTALLED_APPS=[
                'django.contrib.contenttypes',
                'django.contrib.sites',
                'wizard_builder',
                'tests.test_app'
            ],
        )

        import django
        django.setup()

    except ImportError:
        import traceback
        traceback.print_exc()
        raise ImportError('To fix this error, sort out the imports')

    make_migrations()
