from mock import call, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from callisto.delivery.forms import (
    NewSecretKeyForm, SecretKeyForm, SubmitToMatchingForm,
)
from callisto.delivery.models import Report

User = get_user_model()


class SubmitToMatchingFormTest(TestCase):

    def verify_url_works(self, url, expected_result):
        request = {'perp': url}
        form = SubmitToMatchingForm(request)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['perp'], expected_result)

    def verify_url_fails(self, url, expected_error = 'Please enter a valid Facebook profile URL.'):
        request = {'perp': url}
        form = SubmitToMatchingForm(request)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['perp'],
            [expected_error]
        )

    def test_accept_facebook_url(self):
        self.verify_url_works('https://www.facebook.com/kelsey.gilmore.innis', 'kelsey.gilmore.innis')

    def test_accept_partial_url(self):
        self.verify_url_works('facebook.com/kelsey.gilmore.innis', 'kelsey.gilmore.innis')
        self.verify_url_works('www.facebook.com/kelsey.gilmore.innis', 'kelsey.gilmore.innis')
        self.verify_url_works('https://m.facebook.com/kelsey.gilmore.innis', 'kelsey.gilmore.innis')

    def test_accept_with_querystring(self):
        self.verify_url_works('https://www.facebook.com/kate.kirschner1?fref=nf', 'kate.kirschner1')
        self.verify_url_works('https://www.facebook.com/kate.kirschner1/posts/2854650216685?pnref=story', 'kate.kirschner1')

    def test_accept_posts_and_others(self):
        self.verify_url_works('https://www.facebook.com/trendinginchina/videos/600128603423960/', 'trendinginchina')
        self.verify_url_works('https://www.facebook.com/kelsey.gilmore.innis/posts/10106474072154380', 'kelsey.gilmore.innis')
        self.verify_url_works('https://www.facebook.com/jessica.h.ladd/music?pnref=lhc', 'jessica.h.ladd')

    def test_accepts_old_profile_link(self):
        self.verify_url_works('https://www.facebook.com/profile.php?id=100010279981469', '100010279981469')
        self.verify_url_works('www.facebook.com/profile.php?id=100010279981469&fref=nf&pnref=story', '100010279981469')

    def test_non_fb_url_fails(self):
        self.verify_url_fails('https://plus.google.com/101940257310211951398/posts')
        self.verify_url_fails('google.com')
        self.verify_url_fails('https://www.facedbook.com/trendinginchina/videos/600128603423960/')

    def test_non_url_fails(self):
        self.verify_url_fails('notaurl', 'Enter a valid URL.')
        self.verify_url_fails('', 'This field is required.')

    def test_generic_url_fails(self):
        self.verify_url_fails('https://www.facebook.com/messages/10601427')
        self.verify_url_fails('https://www.facebook.com/hashtag/funny?source=feed_text&story_id=858583977551613')
        self.verify_url_fails('https://www.facebook.com/')

class CreateKeyFormTest(TestCase):
    def test_nonmatching_keys_rejected(self):
        bad_request = {'key': 'this is a key',
                       'key2': 'this is also a key'}
        form = NewSecretKeyForm(bad_request)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['key2'],
            ["The two passphrase fields didn't match."]
        )

    def test_matching_keys_accepted(self):
        good_request = {'key': 'this is my good secret key',
                        'key2': 'this is my good secret key'}
        form = NewSecretKeyForm(good_request)
        self.assertTrue(form.is_valid())

    def test_too_short_key_rejected(self):
        bad_request = {'key': 'key',
                       'key2': 'key'}
        form = NewSecretKeyForm(bad_request)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['key'],
            ["Your password isn't strong enough."]
        )

@patch('callisto.delivery.forms.EvalRow.add_report_data')
class DecryptKeyFormTest(TestCase):

    def setUp(self):
        user = User.objects.create(username="dummy", password="dummy")
        self.report = Report(owner = user)
        self.key = '~*~*~*~my key~*~*~*~'
        self.report.encrypt_report('this is a report', self.key)
        self.report.save()

    def test_wrong_key_rejected(self, mock_add_report_data):
        bad_request = {'key': 'not my key'}
        form = SecretKeyForm(bad_request)
        form.report = self.report
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['key'],
            ["The passphrase didn't match."]
        )

    def test_right_key_accepted(self, mock_add_report_data):
        good_request = {'key': self.key}
        form = SecretKeyForm(good_request)
        form.report = self.report
        self.assertTrue(form.is_valid())
