from unittest.mock import MagicMock

from callisto_core.delivery import forms, validators
from callisto_core.delivery.forms import SubmitToMatchingForm
from callisto_core.delivery.models import Report
from mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

User = get_user_model()


class SubmitToMatchingFormTest(TestCase):

    def get_cleaned_identifier(self, url):
        request = {'perp': url}
        form = SubmitToMatchingForm(request)
        self.assertTrue(form.is_valid())
        return form.cleaned_data['perp']

    def verify_url_works(self, url, expected_result):
        self.assertEqual(self.get_cleaned_identifier(url), expected_result)

    def verify_url_fails(self, url, expected_error='Please enter a valid Facebook profile URL.'):
        request = {'perp': url}
        form = SubmitToMatchingForm(request)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['perp'],
            [expected_error]
        )


class SubmitToMatchingFormFacebookTest(SubmitToMatchingFormTest):

    def test_accept_facebook_url(self):
        self.verify_url_works('https://www.facebook.com/callistoorg', 'callistoorg')

    def test_accept_partial_url(self):
        self.verify_url_works('facebook.com/callistoorg', 'callistoorg')
        self.verify_url_works('www.facebook.com/callistoorg', 'callistoorg')
        self.verify_url_works('https://m.facebook.com/callistoorg', 'callistoorg')

    def test_accept_with_querystring(self):
        self.verify_url_works('https://www.facebook.com/callistoorg?fref=nf', 'callistoorg')
        self.verify_url_works(
            'https://www.facebook.com/callistoorg/posts/2854650216685?pnref=story',
            'callistoorg')

    def test_accept_posts_and_others(self):
        self.verify_url_works('https://www.facebook.com/trendinginchina/videos/600128603423960/', 'trendinginchina')
        self.verify_url_works(
            'https://www.facebook.com/callistoorg/posts/10106474072154380',
            'callistoorg')
        self.verify_url_works('https://www.facebook.com/callistoorg/music?pnref=lhc', 'callistoorg')

    def test_accepts_old_profile_link(self):
        self.verify_url_works('https://www.facebook.com/profile.php?id=100010279981469', '100010279981469')
        self.verify_url_works('www.facebook.com/profile.php?id=100010279981469&fref=nf&pnref=story', '100010279981469')
        self.verify_url_works('https://www.facebook.com/people/John-Doe-Jr/100013326345115', '100013326345115')

    def test_non_fb_url_fails(self):
        self.verify_url_fails('https://plus.google.com/101940257310211951398/posts')
        self.verify_url_fails('google.com')
        self.verify_url_fails('https://www.facedbook.com/trendinginchina/videos/600128603423960/')

    def test_non_url_fails(self):
        self.verify_url_fails('notaurl', 'Please enter a valid Facebook profile URL.')
        self.verify_url_fails('', 'This field is required.')

    def test_generic_url_fails(self):
        self.verify_url_fails('https://www.facebook.com/messages/10601427')
        self.verify_url_fails('https://www.facebook.com/hashtag/funny?source=feed_text&story_id=858583977551613')
        self.verify_url_fails('https://www.facebook.com/')

    def test_trims_url(self):
        self.verify_url_works('https://www.facebook.com/callistoorg ', 'callistoorg')
        self.verify_url_works('  https://www.facebook.com/callistoorg/ ', 'callistoorg')
        self.verify_url_works('https://www.facebook.com/callistoorg    ', 'callistoorg')

    def test_case_insensitive(self):
        self.assertEqual(self.get_cleaned_identifier('facebook.com/Callisto_Org'),
                         self.get_cleaned_identifier('https://www.facebook.com/callisto_org'))


@override_settings(CALLISTO_IDENTIFIER_DOMAINS=validators.facebook_or_twitter)
class SubmitToMatchingFormTwitterTest(SubmitToMatchingFormTest):
    expected_error = "Please enter a valid Facebook profile URL or Twitter username/profile URL."

    def test_accept_twitter_url(self):
        self.verify_url_works('https://www.twitter.com/callisto_org', 'twitter:callisto_org')

    def test_accept_partial_url(self):
        self.verify_url_works('twitter.com/callisto_org', 'twitter:callisto_org')
        self.verify_url_works('www.twitter.com/callisto_org', 'twitter:callisto_org')
        self.verify_url_works('https://mobile.twitter.com/callisto_org', 'twitter:callisto_org')

    def test_accept_with_querystring(self):
        self.verify_url_works('https://twitter.com/callisto_org?some=query', 'twitter:callisto_org')

    def test_accept_tweets_and_others(self):
        self.verify_url_works('https://twitter.com/callisto_org/status/857806846668701696', 'twitter:callisto_org')
        self.verify_url_works('https://twitter.com/callisto_org/following', 'twitter:callisto_org')
        self.verify_url_works('https://twitter.com/callisto_org/media', 'twitter:callisto_org')

    def test_non_twitter_url_fails(self):
        self.verify_url_fails('https://plus.google.com/101940257310211951398/posts',
                              expected_error=self.expected_error)
        self.verify_url_fails('google.com', expected_error=self.expected_error)
        self.verify_url_fails('https://www.twittr.com/callisto_org', expected_error=self.expected_error)

    def test_non_url_fails(self):
        self.verify_url_fails('notaurl', expected_error=self.expected_error)
        self.verify_url_fails('', 'This field is required.')

    def test_generic_url_fails(self):
        self.verify_url_fails('https://twitter.com/i/moments', expected_error=self.expected_error)
        self.verify_url_fails('https://support.twitter.com/', expected_error=self.expected_error)
        self.verify_url_fails('https://www.twitter.com/', expected_error=self.expected_error)

    def test_trims_url(self):
        self.verify_url_works('https://www.twitter.com/callisto_org ', 'twitter:callisto_org')
        self.verify_url_works('  https://www.twitter.com/callisto_org ', 'twitter:callisto_org')
        self.verify_url_works('https://www.twitter.com/callisto_org    ', 'twitter:callisto_org')

    def test_still_accepts_facebook(self):
        self.verify_url_works('https://www.facebook.com/callistoorg', 'callistoorg')

    def test_facebook_and_twitter_dont_match_each_other(self):
        self.assertNotEqual(self.get_cleaned_identifier('twitter.com/callisto_org'),
                            self.get_cleaned_identifier('facebook.com/callisto_org'))

    @override_settings(CALLISTO_IDENTIFIER_DOMAINS=validators.twitter_only)
    def test_can_exclude_facebook(self):
        self.verify_url_fails('https://www.facebook.com/callistoorg',
                              expected_error="Please enter a valid Twitter username/profile URL.")

    def test_case_insensitive(self):
        self.assertEqual(self.get_cleaned_identifier('twitter.com/cAlLiStOoRg'),
                         self.get_cleaned_identifier('https://www.twitter.com/CallistoOrg'))

    def test_can_use_at_name(self):
        self.verify_url_works('@callistoorg', 'twitter:callistoorg')
        self.verify_url_fails('@callistoorgtoolong', expected_error=self.expected_error)

    def test_can_override_get_validators(self):
        class CustomSubmitToMatchingForm(SubmitToMatchingForm):
            def get_validators(self):
                return validators.facebook_only
        form = CustomSubmitToMatchingForm({'perp': 'facebook.com/callisto_org'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['perp'], 'callisto_org')
        form = CustomSubmitToMatchingForm({'perp': 'twitter.com/callisto_org'})
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['perp'],
            ['Please enter a valid Facebook profile URL.']
        )


class ReportCreateFormTest(TestCase):

    def test_nonmatching_keys_rejected(self):
        form = forms.ReportCreateForm({
            'key': 'this is a key',
            'key_confirmation': 'this is also a key',
        }, view=MagicMock())
        self.assertFalse(form.is_valid())

    def test_matching_keys_accepted(self):
        form = forms.ReportCreateForm({
            'key': 'this is my good secret key',
            'key_confirmation': 'this is my good secret key',
        }, view=MagicMock())
        self.assertTrue(form.is_valid())


class ReportAccessFormTest(TestCase):

    def test_wrong_key_rejected(self):
        form = forms.ReportAccessForm(
            data={'key': 'not my key'},
            instance=self.report,
            view=MagicMock(),
        )
        form.full_clean()
        self.assertFalse(form.is_valid())
        self.assertFalse(getattr(form, 'decrypted_report', None))

    def test_right_key_accepted(self):
        form = forms.ReportAccessForm(
            data={'key': self.key},
            instance=self.report,
            view=MagicMock(),
        )
        form.full_clean()
        self.assertTrue(form.is_valid())
        self.assertTrue(getattr(form, 'decrypted_report', None))
