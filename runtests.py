#!/usr/bin/env python3

import sys
from django.conf import settings
from django.test.utils import get_runner

from evaluation.tests.test_keypair import public_test_key, private_test_key

settings.configure(
    DEBUG=True,
    USE_TZ=True,
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3"
        }
    },
    #ROOT_URLCONF="",
    INSTALLED_APPS=[
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sites",
        "wizard_builder",
        "delivery",
        "evaluation"
    ],

    CALLISTO_EVAL_PUBLIC_KEY=public_test_key,
    CALLISTO_EVAL_PRIVATE_KEY=private_test_key,
    COORDINATOR_NAME="Coordinator Name",
    KEY_ITERATIONS=100000,
    PASSWORD_MINIMUM_ENTROPY=25,
    SCHOOL_REPORT_PREFIX="000",
    SCHOOL_SHORTNAME="Test School"
)

import django
django.setup()

def run_tests(*test_args):
    if not test_args:
        test_args = ['evaluation/tests'] #['delivery/tests', 'evaluation/tests']

    # Run tests
    TestRunner = get_runner(settings)
    test_runner = TestRunner()

    failures = test_runner.run_tests(test_args)

    if failures:
        sys.exit(bool(failures))


if __name__ == '__main__':
    run_tests(*sys.argv[1:])
