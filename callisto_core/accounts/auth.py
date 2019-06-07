#!/usr/bin/env python3
from hashlib import sha256

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User

from callisto_core.accounts.models import Account


def index(src, length=8):
    """Computes an index suitable for fast lookups on a user record."""
    base = f"{src}//{settings.INDEXING_KEY}"
    cipher = sha256(base.encode('utf-8')).hexdigest()

    return cipher[0:length]


class EncryptedBackend:
    """Authenticates against encrypted credentials stored in the DB."""

    def authenticate(self, request, username, password):
        for user in Account.objects.find(username_index=index(username)):
            if not user or not bcrypt.checkpw(username, user.encrypted_username):
                return None

            if not check_password(password, user.user.password):
                return None

            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
