from django.core.signing import Signer


class StudentVerificationTokenGenerator(object):

    def make_token(self, user):
        '''
        makes a verification token for a user

        Student account verification is spam prevention,
        rather than a security concern. So we can
        make the token the user's signed username

        pls dont spam us??? thanks
        '''
        return Signer().sign(str(user.username)).split(':')[-1]

    def check_token(self, user, token):
        return bool(self.make_token(user) == token)
