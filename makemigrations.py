# script to generate migrations without an implementing Django project


def make_migrations():
    from django.core.management import call_command
    call_command('makemigrations', 'delivery')
    call_command('makemigrations', 'notification')


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
                'callisto.evaluation',
                'callisto.notification',
            ],
            SITE_ID=1,
            APP_URL="test",
            COORDINATOR_NAME="Tatiana Nine",
            CALLISTO_EVAL_PUBLIC_KEY="",
            KEY_ITERATIONS=100,
            ORIGINAL_KEY_ITERATIONS=100000,
            ARGON2_TIME_COST=2,
            ARGON2_MEM_COST=512,
            ARGON2_PARALLELISM=2,
            REPORT_TIME_ZONE='Europe/Paris',
        )

        import django
        django.setup()

    except ImportError:
        import traceback
        traceback.print_exc()
        raise ImportError('To fix this error, sort out the imports')

    make_migrations()
