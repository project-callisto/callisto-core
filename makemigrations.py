# script to generate migrations without an implementing Django project


def make_migrations():
    from django.core.management import call_command
    call_command('makemigrations', 'evaluation')


if __name__ == '__main__':
    import sys
    sys.path.append('./src/')

    try:
        from django.conf import settings

        settings.configure(
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django.contrib.sites',
                'wizard_builder',
                'callisto.delivery',
                'callisto.evaluation'

            ],
            APP_URL="test",
            COORDINATOR_NAME="Tatiana Nine",
            CALLISTO_EVAL_PUBLIC_KEY=""
        )

        import django
        django.setup()

    except ImportError:
        import traceback
        traceback.print_exc()
        raise ImportError('To fix this error, sort out the imports')

    make_migrations()
