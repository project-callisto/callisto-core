# Using callisto-core

Guidance for using callisto-core in your own unique downstream application

## Tenant Configuration

You are likely starting out with 1 tenant, and so will want to lock your SITE_ID to 1 via one or both of these methods

```bash
# bash profile, or similar
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

    CALLISTO_EVAL_PUBLIC_KEY
    CALLISTO_EVAL_PRIVATE_KEY (keep this one secret!)

    # optional
    CALLISTO_CHECK_REPORT_OWNER = True

    # apis, see api section below
    CALLISTO_MATCHING_API
    CALLISTO_NOTIFICATION_API
    CALLISTO_TENANT_API
```

- GPG
- tenant specific

## APIs

### View Functions

View partials provide all the callisto-core front-end functionality. Subclass these partials with your own views if you are implementing callisto-core.

The `views.py` files in this repo are specific to callisto-core. If you are implementing callisto-core you SHOULD NOT be importing these views. Import from `view_partials` instead, and implement classes that look like the ones in `views`.

### NotificationApi

Use this to change your notification (eg. emails, PDFs, slack messages, etc) implementation

### MatchingApi

Use this to change your matching implementation

## Data

- sites
- questions
- notifications
