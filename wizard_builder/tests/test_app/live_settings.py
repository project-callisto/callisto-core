from wizard_builder.tests.test_app.settings import *

DEBUG = False

MIDDLEWARE_CLASSES = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
] + MIDDLEWARE_CLASSES
