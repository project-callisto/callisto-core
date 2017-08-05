#!/usr/bin/env python

import os
from wizard_builder.tests.test_app.manage import main

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wizard_builder.tests.test_app.app_settings")
    main()
