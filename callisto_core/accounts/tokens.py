import logging

from django.core.signing import Signer

logger = logging.getLogger(__name__)


class StudentVerificationTokenGenerator(object):
    def make_token(self, user):
        """
        makes a verification token for a user

        Student account verification is spam prevention,
        rather than a security concern. So we can
        make the token the user's signed uuid
        """
        return Signer().sign(str(user.account.uuid)).split(":")[-1]

    def check_token(self, user, token):
        return bool(self.make_token(user) == token)
