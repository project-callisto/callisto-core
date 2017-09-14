# Using callisto-core

Guidance for using callisto-core in your own unique downstream application

## Tenant Configuration

You are likely starting out with 1 tenant, and so will want to lock your SITE_ID to 1 via one of both of these methods

```bash
export SITE_ID=1
```

```python
# settings.py
SITE_ID = 1
```

## Settings

django settings.py minimum requirements

```python
    # the defaults, wizard builder and its requirements, the callisto-core apps
    INSTALLED_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.sites',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'nested_admin',
        'tinymce',
        'widget_tweaks',
        'wizard_builder',
        'callisto_core.delivery',
        'callisto_core.evaluation',
        'callisto_core.notification',
        'callisto_core.reporting',
    ]

    # the default generated MIDDLEWARE_CLASSES
    MIDDLEWARE_CLASSES = [
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'django.middleware.security.SecurityMiddleware',
    ]

    # encryption handling
    KEY_HASHERS = [
        "callisto_core.delivery.hashers.Argon2KeyHasher",
        "callisto_core.delivery.hashers.PBKDF2KeyHasher"
    ]

    # tenant specific
    COORDINATOR_NAME
    COORDINATOR_EMAIL
    SCHOOL_SHORTNAME
    SCHOOL_LONGNAME
    SCHOOL_REPORT_PREFIX
    COORDINATOR_PUBLIC_KEY
    CALLISTO_EVAL_PUBLIC_KEY
    CALLISTO_EVAL_PUBLIC_KEY

    # optional
    MATCH_IMMEDIATELY = True
    CALLISTO_CHECK_REPORT_OWNER = False

    # apis, see api section below
    CALLISTO_MATCHING_API
    CALLISTO_NOTIFICATION_API
```

- GPG (WIP)
- tenant specific (WIP)

## Views

### views.py

Views specific to callisto-core, if you are implementing callisto-core you SHOULD NOT be importing these views. Import from view_partials instead. All of the classes in this file should represent one of more HTML view.

### view_partials.py

View partials provide all the callisto-core front-end functionality. Subclass these partials with your own views if you are implementing callisto-core. Many of the view partials only provide a subset of the functionality required for a full HTML view.

## Data

- sites (WIP)
- questions (WIP)
- notifications (WIP)

## Apis

- notification (WIP)
- matching (WIP)
