import os
import sys

try:
    from django.conf import settings
    from django.test.utils import get_runner

    os.environ['DJANGO_SETTINGS_MODULE'] = 'wizard_builder.tests.settings'

    try:
        import django
        setup = django.setup
    except AttributeError:
        pass
    else:
        setup()

except ImportError:
    # TODO: remove, this error message is no longer accurate for most cases
    import traceback
    traceback.print_exc()
    raise ImportError("To fix this error, run: pip install -r requirements-test.txt")


def run_tests(*test_args):
    if not test_args:
        test_args = ['wizard_builder.tests']

    # Run tests
    TestRunner = get_runner(settings)
    test_runner = TestRunner()

    failures = test_runner.run_tests(test_args)

    if failures:
        sys.exit(bool(failures))


if __name__ == '__main__':
    run_tests(*sys.argv[1:])
