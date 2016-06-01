import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from unittest.mock import patch, Mock

User = get_user_model()

from wizard_builder.models import SingleLineText, RadioButton, Choice, QuestionPage
from wizard_builder.forms import QuestionPageForm

from ..models import Report
from ..wizard import EncryptedFormWizard
from ..forms import NewSecretKeyForm, SecretKeyForm
from evaluation.models import EvalRow


def sort_json(text):
    return sorted(json.loads(text), key=lambda x: x['id'])


def get_body(response):
    return response.content.decode('utf-8')


class RecordFormBaseTest(TestCase):
    def setUp(self):
        self.page1 = QuestionPage.objects.create()
        self.page2 = QuestionPage.objects.create()
        self.question1 = SingleLineText.objects.create(text="first question", page=self.page1)
        self.question2 = SingleLineText.objects.create(text="2nd question", page=self.page2)

    def _get_wizard_response(self, wizard, form_list, **kwargs):
        # simulate what wizard does on final form submit
        wizard.processed_answers = wizard.process_answers(form_list=form_list, form_dict=dict(enumerate(form_list)))
        return get_body(wizard.done(form_list=form_list, form_dict=dict(enumerate(form_list)), **kwargs))

class RecordFormIntegratedTest(RecordFormBaseTest):

    def setUp(self):
        super().setUp()
        User.objects.create_user(username='dummy', password='dummy')
        self.client.login(username='dummy', password='dummy')
        self.request = HttpRequest()
        self.request.GET = {}
        self.request.method = 'GET'
        self.request.user = User.objects.get(username='dummy')


    #TODO: test edit by non-owning user

    record_form_url = '/reports/new/0/'
    report_key = 'solidasarock1234rock'

    def test_new_record_page_renders_record_template(self):
        response = self.client.get(self.record_form_url)
        self.assertTemplateUsed(response, 'record_form.html')

    def test_wizard_generates_correct_number_of_pages(self):
        page3 = QuestionPage.objects.create()
        SingleLineText.objects.create(text="first page question", page=page3)
        SingleLineText.objects.create(text="one more first page question", page=page3, position=2)
        SingleLineText.objects.create(text="another first page question", page=page3, position=1)
        wizard = EncryptedFormWizard.wizard_factory()()
        #includes key page
        self.assertEqual(len(wizard.form_list), 4)

    def test_wizard_appends_key_page(self):
        wizard = EncryptedFormWizard.wizard_factory()()
        self.assertEqual(len(wizard.form_list), 3)
        self.assertEqual(wizard.form_list[-1], NewSecretKeyForm)

    @patch('delivery.wizard.Report')
    def test_wizard_done_redirects_to_dashboard(self, mockReport):
        wizard = EncryptedFormWizard.wizard_factory()()
        PageOneForm = wizard.form_list[0]
        PageTwoForm = wizard.form_list[1]
        KeyForm = wizard.form_list[2]
        page_one = PageOneForm({'question_%i' % self.question1.pk: ""})
        page_one.is_valid()
        page_two = PageTwoForm({'question_%i' % self.question2.pk: ""})
        page_two.is_valid()
        key_form = KeyForm({'key': self.report_key, 'key2': self.report_key})
        key_form.is_valid()
        form_list=[page_one, page_two, key_form]
        wizard.processed_answers = wizard.process_answers(form_list=form_list, form_dict=dict(enumerate(form_list)))
        response = wizard.done(form_list=form_list, form_dict=dict(enumerate(form_list)), request=self.request)
        self.assertEqual(response.url, '/reports/dashboard')

    @patch('delivery.wizard.Report')
    def test_done_serializes_questions(self, mockReport):
        self.maxDiff = None

        radio_button_q = RadioButton.objects.create(text="this is a radio button question", page=self.page2)
        for i in range(5):
            Choice.objects.create(text="This is choice %i" % i, question=radio_button_q)
        wizard = EncryptedFormWizard.wizard_factory()()

        PageOneForm = wizard.form_list[0]
        PageTwoForm = wizard.form_list[1]
        KeyForm = wizard.form_list[2]

        page_one = PageOneForm({'question_%i' % self.question1.pk: 'test answer'})
        page_one.is_valid()
        page_two = PageTwoForm({'question_%i' % self.question2.pk: 'another answer to a different question',
                                'question_%i' % radio_button_q.pk: radio_button_q.choice_set.all()[2].pk})
        page_two.is_valid()
        key_form = KeyForm({'key': self.report_key, 'key2': self.report_key})
        key_form.is_valid()

        object_ids = [choice.pk for choice in radio_button_q.choice_set.all()]
        selected_id = object_ids[2]
        object_ids.insert(0, radio_button_q.pk)
        object_ids.insert(0, selected_id)
        object_ids.insert(0, self.question2.pk)
        object_ids.insert(0, self.question1.pk)

        json_report = """[
    { "answer": "test answer",
      "id": %i,
      "section": 1,
      "question_text": "first question",
      "type": "SingleLineText"
    },
    { "answer": "another answer to a different question",
      "id": %i,
      "section": 1,
      "question_text": "2nd question",
      "type": "SingleLineText"
    },
    { "answer": "%i",
      "id": %i,
      "section": 1,
      "question_text": "this is a radio button question",
            "choices": [{"id": %i, "choice_text": "This is choice 0"},
                  {"id": %i, "choice_text": "This is choice 1"},
                  {"id": %i, "choice_text": "This is choice 2"},
                  {"id": %i, "choice_text": "This is choice 3"},
                  {"id": %i, "choice_text": "This is choice 4"}],
      "type": "RadioButton"
    }
  ]""" % tuple(object_ids)

        mock_report = Report()
        mock_report.save = Mock()
        mock_report.owner = self.request.user
        mockReport.return_value = mock_report

        def check_json():
            self.assertEqual(sort_json(mock_report.decrypted_report(self.report_key)),
                             sort_json(json_report))

        mock_report.save.side_effect = check_json

        self._get_wizard_response(wizard, form_list=[page_one, page_two, key_form], request = self.request)
        mock_report.save.assert_any_call()

    @patch('delivery.wizard.Report')
    @patch('delivery.wizard.EvalRow')
    def test_done_saves_anonymised_qs(self, mockEvalRow, mockReport):
        self.maxDiff = None

        radio_button_q = RadioButton.objects.create(text="this is a radio button question", page=self.page2)
        for i in range(5):
            Choice.objects.create(text="This is choice %i" % i, question = radio_button_q)
        wizard = EncryptedFormWizard.wizard_factory()()

        PageOneForm = wizard.form_list[0]
        PageTwoForm = wizard.form_list[1]
        KeyForm = wizard.form_list[2]

        page_one = PageOneForm({'question_%i' % self.question1.pk: 'test answer'})
        page_one.is_valid()
        page_two = PageTwoForm({'question_%i' % self.question2.pk: 'another answer to a different question',
                                'question_%i' % radio_button_q.pk: radio_button_q.choice_set.all()[2].pk})
        page_two.is_valid()
        key_form = KeyForm({'key': self.report_key, 'key2': self.report_key})
        key_form.is_valid()

        mock_report = Report()
        mock_report.save = Mock()
        mock_report.owner = self.request.user
        mockReport.return_value = mock_report

        mock_eval_row = EvalRow()
        mock_eval_row.save = Mock()
        mockEvalRow.return_value = mock_eval_row

        self._get_wizard_response(wizard, form_list=[page_one, page_two, key_form], request = self.request)
        mock_eval_row.save.assert_any_call()

class EditRecordFormTest(RecordFormBaseTest):
    record_form_url = '/reports/edit/%s/'

    def setUp(self):
        super().setUp()

        User.objects.create_user(username='dummy', password='dummy')
        self.client.login(username='dummy', password='dummy')
        self.request = HttpRequest()
        self.request.GET = {}
        self.request.method = 'GET'
        self.request.user = User.objects.get(username='dummy')

        self.report_text = """[
    { "answer": "test answer",
      "id": %i,
      "section": 1,
      "question_text": "first question",
      "type": "SingleLineText"
    },
    { "answer": "another answer to a different question",
      "id": %i,
      "section": 1,
      "question_text": "2nd question",
      "type": "SingleLineText"
    }
  ]""" % (self.question1.pk, self.question2.pk)
        self.report = Report(owner = self.request.user)
        self.report_key = 'bananabread! is not my key'
        self.report.encrypt_report(self.report_text, self.report_key)
        self.report.save()
        row = EvalRow()
        row.anonymise_record(action=EvalRow.CREATE, report=self.report, decrypted_text=self.report_text)
        row.save()

    def enter_edit_key(self):
        return self.client.post(
            (self.record_form_url % self.report.pk),
            data={'0-key': self.report_key,
                  'wizard_goto_step':1,
                  'form_wizard' + str(self.report.id) + '-current_step': 0},
            follow=True
        )

    def test_edit_record_page_renders_key_prompt(self):
        response = self.client.get(self.record_form_url % self.report.pk, follow=True)
        self.assertTemplateUsed(response, 'decrypt_record_for_edit.html')
        self.assertIsInstance(response.context['form'], SecretKeyForm)

    def test_edit_record_form_advances_to_second_page(self):
        response = self.enter_edit_key()
        self.assertTemplateUsed(response, 'record_form.html')
        self.assertIsInstance(response.context['form'], QuestionPageForm)
        self.assertContains(response, 'name="1-question_%i"' % self.question1.pk)
        self.assertNotContains(response, 'name="1-question_%i"' % self.question2.pk)

    def test_initial_is_passed_to_forms(self):
        response = self.enter_edit_key()
        form = response.context['form']
        self.assertIn('test answer', form.initial.values())
        self.assertIn('another answer to a different question', form.initial.values())

    def edit_record(self, record_to_edit):
        wizard = EncryptedFormWizard.wizard_factory(object_to_edit=record_to_edit)()

        KeyForm1 = wizard.form_list[0]
        PageOneForm = wizard.form_list[1]
        PageTwoForm = wizard.form_list[2]
        KeyForm2 = wizard.form_list[3]

        key_form_1 = KeyForm1({'key': self.report_key})
        key_form_1.is_valid()

        page_one = PageOneForm({'question_%i' % self.question1.pk: 'test answer'})
        page_one.is_valid()
        page_two = PageTwoForm({'question_%i' % self.question2.pk: 'edited answer to second question',})
        page_two.is_valid()
        key_form_2 = KeyForm2({'key': self.report_key})
        key_form_2.is_valid()

        self._get_wizard_response(wizard, form_list=[key_form_1, page_one, page_two, key_form_2], request = self.request)

    def test_edit_modifies_record(self):
        self.maxDiff = None

        json_report = """[
    { "answer": "test answer",
      "id": %i,
      "section": 1,
      "question_text": "first question",
      "type": "SingleLineText"
    },
    { "answer": "edited answer to second question",
      "id": %i,
      "section": 1,
      "question_text": "2nd question",
      "type": "SingleLineText"
    }
  ]"""  % (self.question1.pk, self.question2.pk)

        self.edit_record(self.report)
        self.assertEqual(Report.objects.count(), 1)
        self.assertEqual(sort_json(Report.objects.get(id=self.report.pk).decrypted_report(self.report_key)),
                         sort_json(json_report))

    def test_cant_edit_with_bad_key(self):
        self.maxDiff = None

        wizard = EncryptedFormWizard.wizard_factory(object_to_edit=self.report)()

        KeyForm1 = wizard.form_list[0]

        key_form_1 = KeyForm1({'key': "not the right key!!!"})
        self.assertFalse(key_form_1.is_valid())

    def test_cant_save_edit_with_bad_key(self):
        wizard = EncryptedFormWizard.wizard_factory(object_to_edit=self.report)()

        KeyForm1 = wizard.form_list[0]
        PageOneForm = wizard.form_list[1]
        PageTwoForm = wizard.form_list[2]
        KeyForm2 = wizard.form_list[3]

        key_form_1 = KeyForm1({'key': self.report_key})
        key_form_1.is_valid()

        page_one = PageOneForm({'question_%i' % self.question1.pk: 'test answer'})
        page_one.is_valid()
        page_two = PageTwoForm({'question_%i' % self.question2.pk: 'edited answer to second question',})
        page_two.is_valid()
        key_form_2 = KeyForm2({'key': "not the right key"})
        self.assertFalse(key_form_2.is_valid())
        with self.assertRaises(KeyError):
            self._get_wizard_response(wizard, form_list=[key_form_1, page_one, page_two, key_form_2], request = self.request)
        self.assertEqual(sort_json(Report.objects.get(id=self.report.pk).decrypted_report(self.report_key)),
                         sort_json(self.report_text))

    def test_edit_saves_anonymous_row(self):
        self.edit_record(self.report)
        self.assertEqual(EvalRow.objects.count(), 2)
        self.assertEqual(EvalRow.objects.last().action, EvalRow.EDIT)
        self.edit_record(self.report)
        self.assertEqual(EvalRow.objects.count(), 3)
        self.assertEqual(Report.objects.count(), 1)

    def test_edit_saves_original_record_if_no_data_exists(self):
        old_report = Report(owner = self.request.user)
        old_report.encrypt_report(self.report_text, self.report_key)
        old_report.save()

        self.assertEqual(EvalRow.objects.count(), 1)
        self.assertEqual(EvalRow.objects.filter(action=EvalRow.FIRST).count(), 0)

        self.edit_record(record_to_edit=old_report)
        self.assertEqual(EvalRow.objects.count(), 3)
        self.assertEqual(EvalRow.objects.filter(action=EvalRow.FIRST).count(), 1)
        self.assertEqual(EvalRow.objects.last().action, EvalRow.EDIT)
        self.assertEqual(EvalRow.objects.filter(action=EvalRow.FIRST).first().record_identifier, EvalRow.objects.last().record_identifier)
        self.assertNotEqual(EvalRow.objects.filter(action=EvalRow.FIRST).first().row, EvalRow.objects.last().row)
