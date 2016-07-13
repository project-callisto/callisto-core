import inspect
import json
from unittest import skip

from tests.test_app.views import TestWizard
from wizard_builder.forms import QuestionPageForm, TextPageForm
from wizard_builder.models import (
    Checkbox, Choice, Conditional, Date, QuestionPage, RadioButton,
    SingleLineText, TextPage,
)
from wizard_builder.views import (
    ConfigurableFormWizard, calculate_page_count_map,
)

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.test import TestCase

User = get_user_model()


def sort_json(text):
    return sorted(json.loads(text), key=lambda x: x['id'])


def get_body(response):
    return response.content.decode('utf-8')


class FormBaseTest(TestCase):

    def setUp(self):
        self.page1 = QuestionPage.objects.create()
        self.page2 = QuestionPage.objects.create()
        self.question1 = SingleLineText.objects.create(text="first question", page=self.page1)
        self.question2 = SingleLineText.objects.create(text="2nd question", page=self.page2)

    def _get_wizard_response(self, wizard, form_list, **kwargs):
        # simulate what wizard does on final form submit
        wizard.processed_answers = wizard.process_answers(form_list=form_list, form_dict=dict(enumerate(form_list)))
        return get_body(wizard.done(form_list=form_list, form_dict=dict(enumerate(form_list)), **kwargs))


class WizardIntegratedTest(FormBaseTest):

    def setUp(self):
        super(WizardIntegratedTest, self).setUp()
        User.objects.create_user(username='dummy', password='dummy')
        self.client.login(username='dummy', password='dummy')
        self.request = HttpRequest()
        self.request.GET = {}
        self.request.method = 'GET'
        self.request.user = User.objects.get(username='dummy')

    form_url = '/wizard/0/'
    report_key = 'solidasarock1234rock'

    def _answer_page_one(self):
        return self.client.post(
            self.form_url,
            data={'0-question_%i' % self.question1.pk: 'test answer',
                  'wizard_goto_step': 1,
                  'form_wizard-current_step': 0},
            follow=True)

    def _answer_page_two(self, response):
        return self.client.post(
            response.redirect_chain[0][0],
            data={'1-question_%i' % self.question2.pk: 'another answer to a different question',
                  'wizard_goto_step': 2,
                  'form_wizard-current_step': 1},
            follow=True)

    def test_wizard_generates_correct_number_of_pages(self):
        page3 = QuestionPage.objects.create()
        SingleLineText.objects.create(text="first page question", page=page3)
        SingleLineText.objects.create(text="one more first page question", page=page3, position=2)
        SingleLineText.objects.create(text="another first page question", page=page3, position=1)
        wizard = ConfigurableFormWizard.wizard_factory()()
        self.assertEqual(len(wizard.form_list), 3)

    def test_question_pages_without_questions_are_filtered_out(self):
        # empty_page
        QuestionPage.objects.create()
        wizard = TestWizard.wizard_factory()()
        self.assertEqual(len(wizard.form_list), 2)
        self.assertIn(QuestionPageForm, inspect.getmro(wizard.form_list[0]))
        self.assertNotIn(TextPageForm, inspect.getmro(wizard.form_list[-1]))

    def test_text_pages_are_included(self):
        TextPage.objects.create(title="this page title", text="some text goes here", position=0)
        self.page1.position = 1
        self.page1.save()
        wizard = TestWizard.wizard_factory()()
        page_one_form = wizard.form_list[0]({})

        self.assertEqual(len(wizard.form_list), 3)
        self.assertEqual(page_one_form.title, "this page title")
        self.assertTrue(page_one_form.is_valid())

    def test_displays_first_page(self):
        response = self.client.get(self.form_url)
        self.assertIsInstance(response.context['form'], QuestionPageForm)
        self.assertContains(response, 'name="0-question_%i"' % self.question1.pk)
        self.assertNotContains(response, 'name="0-question_%i"' % self.question2.pk)

    def test_form_advances_to_second_page(self):
        response = self.client.post(
            self.form_url,
            data={'0-question_%i"' % self.question1.pk: 'A new report',
                  'wizard_goto_step': 1,
                  'form_wizard-current_step': 0},
            follow=True)

        self.assertTrue(response.redirect_chain[0][0].endswith("/wizard/1/"))
        self.assertContains(response, 'name="1-question_%i"' % self.question2.pk)
        self.assertNotContains(response, 'name="1-question_%i"' % self.question1.pk)

    def test_can_alter_form_without_restarting_server(self):
        new_question = SingleLineText.objects.create(text="another first page question", page=self.page1)
        response = self.client.get(self.form_url)
        self.assertContains(response, 'name="0-question_%i"' % new_question.pk)

    def test_done_serializes_questions(self):
        self.maxDiff = None

        radio_button_q = RadioButton.objects.create(text="this is a radio button question", page=self.page2)
        for i in range(5):
            Choice.objects.create(text="This is choice %i" % i, question=radio_button_q)

        response = self._answer_page_one()
        response = self.client.post(
            response.redirect_chain[0][0],
            data={'1-question_%i' % self.question2.pk: 'another answer to a different question',
                  '1-question_%i' % radio_button_q.pk: radio_button_q.choice_set.all()[2].pk,
                  'wizard_goto_step': 2,
                  'form_wizard-current_step': 1},
            follow=True)

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

        self.assertEqual(sort_json(get_body(response)), sort_json(json_report))

    @skip("needs fixing")
    def test_form_saves_answer_of_deleted_question(self):
        self.maxDiff = None
        question3 = SingleLineText.objects.create(text="3rd question", page=self.page2)

        response = self._answer_page_one()

        deleted_question_pk = question3.pk
        question3.delete()

        response = self.client.post(
            response.redirect_chain[0][0],
            data={'1-question_%i' % self.question2.pk: 'another answer to a different question',
                  '1-question_%i' % deleted_question_pk: 'answer to deleted question',
                  'wizard_goto_step': 2,
                  'form_wizard-current_step': 1},
            follow=True)

        output = get_body(response)
        self.assertRaises(SingleLineText.DoesNotExist, SingleLineText.objects.get, pk=deleted_question_pk)
        self.assertIn('3rd', output)
        self.assertIn('answer to deleted question', output)

    @skip("needs fixing")
    def test_form_saves_answer_of_updated_question(self):
        self.maxDiff = None

        response = self._answer_page_one()

        self.question1.text = "1st question UPDATED"
        self.question1.save()

        response = self.client.post(
            response.redirect_chain[0][0],
            data={'1-question_%i' % self.question2.pk: 'another answer to a different question',
                  'wizard_goto_step': 2,
                  'form_wizard-current_step': 1},
            follow=True)

        output = get_body(response)
        self.assertIn('UPDATED', SingleLineText.objects.get(pk=self.question1.pk).text)
        self.assertIn('test answer', output)
        self.assertNotIn('UPDATED', output)

    @skip("needs fixing")
    def test_form_saves_deleted_choice_selection(self):
        radio_button_q = RadioButton.objects.create(text="this is a radio button question", page=self.page1)
        for i in range(5):
            if i == 2:
                Choice.objects.create(text="This is DELETED choice %i" % i, question=radio_button_q)
            else:
                Choice.objects.create(text="This is choice %i" % i, question=radio_button_q)

        deleted_pk = radio_button_q.choice_set.all()[2].pk

        response = self.client.post(
            self.form_url,
            data={'0-question_%i' % self.question1.pk: 'test answer',
                  '0-question_%i' % radio_button_q.pk: deleted_pk,
                  'wizard_goto_step': 1,
                  'form_wizard-current_step': 0},
            follow=True)

        Choice.objects.get(pk=deleted_pk).delete()
        response = self._answer_page_two(response)

        output = get_body(response)
        self.assertRaises(Choice.DoesNotExist, Choice.objects.get, pk=deleted_pk)
        self.assertIn('This is DELETED choice', output)

    @skip("needs fixing")
    def test_form_saves_updated_choice_selection(self):
        radio_button_q = RadioButton.objects.create(text="this is a radio button question", page=self.page1)
        for i in range(5):
            Choice.objects.create(text="This is choice %i" % i, question=radio_button_q)

        updated_pk = radio_button_q.choice_set.all()[4].pk

        response = self.client.post(
            self.form_url,
            data={'0-question_%i' % self.question1.pk: 'test answer',
                  '0-question_%i' % radio_button_q.pk: updated_pk,
                  'wizard_goto_step': 1,
                  'form_wizard-current_step': 0},
            follow=True)

        updated_choice = Choice.objects.get(pk=updated_pk)
        updated_choice.text = "This is choice 4 UPDATED"
        updated_choice.save()

        response = self._answer_page_two(response)

        output = get_body(response)
        self.assertIn('UPDATED', Choice.objects.get(pk=updated_pk).text)
        self.assertIn('This is choice 4', output)
        self.assertNotIn('UPDATED', output)

    def test_form_saves_date(self):
        date_q = Date.objects.create(text="When did it happen?", page=self.page2)

        response = self._answer_page_one()
        response = self.client.post(
            response.redirect_chain[0][0],
            data={'1-question_%i' % self.question2.pk: 'another answer to a different question',
                  '1-question_%i' % date_q.pk: '7/4/15',
                  'wizard_goto_step': 2,
                  'form_wizard-current_step': 1},
            follow=True)
        output = get_body(response)
        self.assertIn('7/4/15', output)

    def test_form_saves_checkboxes(self):
        checkbox_q = Checkbox.objects.create(text="this is a checkbox question", page=self.page2)
        for i in range(5):
            Choice.objects.create(text="This is checkbox choice %i" % i, question=checkbox_q)
        selected_1 = checkbox_q.choice_set.all()[0].pk
        selected_2 = checkbox_q.choice_set.all()[4].pk

        response = self._answer_page_one()
        response = self.client.post(
            response.redirect_chain[0][0],
            data={'1-question_%i' % self.question2.pk: 'another answer to a different question',
                  '1-question_%i' % checkbox_q.pk: [str(selected_1), str(selected_2)],
                  'wizard_goto_step': 2,
                  'form_wizard-current_step': 1},
            follow=True)
        output = get_body(response)
        self.assertIn("checkbox choice", output)
        self.assertIn('["%i", "%i"]' % (selected_1, selected_2), output)

    def test_pages_with_multiple(self):
        multiple_page = QuestionPage.objects.create(multiple=True, name_for_multiple="form")
        q1 = SingleLineText.objects.create(text="question 1", page=multiple_page)
        q2 = SingleLineText.objects.create(text="question 2", page=multiple_page)

        response = self._answer_page_one()
        response = self._answer_page_two(response)
        response = self.client.post(
            response.redirect_chain[0][0],
            data={"2-TOTAL_FORMS": 2,
                  "2-INITIAL_FORMS": 0,
                  '2-0-question_%i' % q1.pk: "question 1 first answer",
                  '2-0-question_%i' % q2.pk: "question 2 first answer",
                  '2-1-question_%i' % q1.pk: "question 1 second answer",
                  '2-1-question_%i' % q2.pk: "question 2 second answer",
                  'wizard_goto_step': 3,
                  'form_wizard-current_step': 2},
            follow=True)

        output = json.loads(get_body(response))
        self.assertEqual(multiple_page.pk, output[2]['page_id'])
        answers = [sort_json(json.dumps(answer)) for answer in output[2]['answers']]
        self.assertEquals("question 1 first answer", answers[0][0]['answer'])
        self.assertEquals("question 2 first answer", answers[0][1]['answer'])
        self.assertEquals("question 1 second answer", answers[1][0]['answer'])
        self.assertEquals("question 2 second answer", answers[1][1]['answer'])

    def test_pages_with_extra(self):
        self.maxDiff = None
        self.page1.delete()
        self.page2.delete()
        page3 = QuestionPage.objects.create()
        question1 = RadioButton.objects.create(text="this is a radio button question", page=page3)
        for i in range(5):
            choice = Choice.objects.create(text="This is choice %i" % i, question=question1)
            if i == 0:
                choice.extra_info_placeholder = "extra box for choice %i" % i
                choice.save()
        question2 = RadioButton.objects.create(text="this is another radio button question", page=page3)
        for i in range(5):
            choice = Choice.objects.create(text="This is choice %i" % i, question=question2)
            if i % 2 == 1:
                choice.extra_info_placeholder = "extra box for choice %i" % i
                choice.save()
        question3 = RadioButton.objects.create(text="this is a radio button question too", page=page3)
        for i in range(5):
            choice = Choice.objects.create(text="This is choice %i" % i, question=question3)
            if i == 0:
                choice.extra_info_placeholder = "extra box for choice %i" % i
                choice.save()

        response = self.client.post(
            self.form_url,
            data={'0-question_%i' % question1.pk: question1.choice_set.all()[1].pk,
                  '0-question_%i_extra-%i' % (question1.pk, question1.choice_set.all()[0].pk):
                      "this shouldn't be in the report",
                  '0-question_%i' % question2.pk: question2.choice_set.all()[3].pk,
                  '0-question_%i_extra-%i' % (question2.pk, question2.choice_set.all()[1].pk):
                      "this shouldn't be in the report either",
                  '0-question_%i_extra-%i' % (question2.pk, question2.choice_set.all()[3].pk):
                      "this should be in the report",
                  '0-question_%i' % question3.pk: question3.choice_set.all()[0].pk,
                  'wizard_goto_step': 1,
                  'form_wizard-current_step': 0},
            follow=True)

        first_q_object_ids = [q_choice.pk for q_choice in question1.choice_set.all()]
        selected_id = first_q_object_ids[1]
        first_q_object_ids.insert(0, question1.pk)
        first_q_object_ids.insert(0, selected_id)
        first_q_output = """{
          "answer": "%i",
          "id": %i,
          "question_text": "this is a radio button question",
                "choices": [{"id": %i, "choice_text": "This is choice 0"},
                      {"id": %i, "choice_text": "This is choice 1"},
                      {"id": %i, "choice_text": "This is choice 2"},
                      {"id": %i, "choice_text": "This is choice 3"},
                      {"id": %i, "choice_text": "This is choice 4"}],
          "type": "RadioButton",
          "section": 1
         }""" % tuple(first_q_object_ids)

        second_q_object_ids = [q_choice.pk for q_choice in question2.choice_set.all()]
        selected_id = second_q_object_ids[3]
        second_q_object_ids.insert(0, question2.pk)
        second_q_object_ids.insert(0, selected_id)
        second_q_output = """{
          "answer": "%i",
          "id": %i,
          "question_text": "this is another radio button question",
                "choices": [{"id": %i, "choice_text": "This is choice 0"},
                      {"id": %i, "choice_text": "This is choice 1"},
                      {"id": %i, "choice_text": "This is choice 2"},
                      {"id": %i, "choice_text": "This is choice 3"},
                      {"id": %i, "choice_text": "This is choice 4"}],
          "type": "RadioButton",
          "section": 1,
          "extra": {
                    "extra_text": "extra box for choice 3",
                    "answer": "this should be in the report"
                    }
         }""" % tuple(second_q_object_ids)

        third_q_object_ids = [q_choice.pk for q_choice in question3.choice_set.all()]
        selected_id = third_q_object_ids[0]
        third_q_object_ids.insert(0, question3.pk)
        third_q_object_ids.insert(0, selected_id)
        third_q_output = """{
          "answer": "%i",
          "id": %i,
          "section": 1,
          "question_text": "this is a radio button question too",
                "choices": [{"id": %i, "choice_text": "This is choice 0"},
                      {"id": %i, "choice_text": "This is choice 1"},
                      {"id": %i, "choice_text": "This is choice 2"},
                      {"id": %i, "choice_text": "This is choice 3"},
                      {"id": %i, "choice_text": "This is choice 4"}],
          "type": "RadioButton",
          "extra": {
                    "extra_text": "extra box for choice 0",
                    "answer": ""
                    }
         }""" % tuple(third_q_object_ids)

        desired_output = ("[%s, %s, %s]" % (first_q_output, second_q_output, third_q_output))
        output = get_body(response)
        self.assertEqual(sort_json(desired_output), sort_json(output))


class PageCountTest(FormBaseTest):

    def test_only_question_pages_are_counted(self):
        page3 = TextPage.objects.create()
        pages = [self.page1, self.page2, page3]
        self.assertEqual(calculate_page_count_map(pages)[0], 1)
        self.assertEqual(calculate_page_count_map(pages)[1], 2)
        self.assertEqual(calculate_page_count_map(pages)['page_count'], 2)

    def test_collapses_conditional_branches(self):
        page1a = QuestionPage.objects.create()
        SingleLineText.objects.create(text="first conditional question", page=page1a)
        Conditional.objects.create(condition_type=Conditional.EXACTLY, page=page1a, question=self.question1,
                                   answer="whatever")
        page1b = QuestionPage.objects.create()
        SingleLineText.objects.create(text="second conditional question", page=page1b)
        Conditional.objects.create(condition_type=Conditional.EXACTLY, page=page1b, question=self.question1,
                                   answer="whatever")
        page2a = QuestionPage.objects.create()
        SingleLineText.objects.create(text="single conditional question", page=page2a)
        Conditional.objects.create(condition_type=Conditional.EXACTLY, page=page2a, question=self.question2,
                                   answer="whatever again")
        pages = [self.page1, self.page2, page1a, page1b, page2a]
        self.assertEqual(calculate_page_count_map(pages)[0], 1)
        self.assertEqual(calculate_page_count_map(pages)[1], 2)
        self.assertEqual(calculate_page_count_map(pages)[2], 3)
        self.assertEqual(calculate_page_count_map(pages)[3], 3)
        self.assertEqual(calculate_page_count_map(pages)[4], 4)
        self.assertEqual(calculate_page_count_map(pages)['page_count'], 4)

# TODO: re-enable below when separate app
#
# class EditRecordFormTest(RecordFormBaseTest):
#     form_url = '/reports/edit/%s/'
#
#     def setUp(self):
#         super().setUp()
#         self.report_text = """[
#     { "answer": "test answer",
#       "id": %i,
#       "section": 1,
#       "question_text": "first question",
#       "type": "SingleLineText"
#     },
#     { "answer": "another answer to a different question",
#       "id": %i,
#       "section": 1,
#       "question_text": "2nd question",
#       "type": "SingleLineText"
#     }
#   ]""" % (self.question1.pk, self.question2.pk)
#         self.report = Report(owner = self.request.user)
#         self.report_key = 'bananabread! is not my key'
#         self.report.encrypt_report(self.report_text, self.report_key)
#         self.report.save()
#         row = EvalRow()
#         row.anonymise_record(action=EvalRow.CREATE, report=self.report, decrypted_text=self.report_text)
#         row.save()
#
#     def enter_edit_key(self):
#         return self.client.post(
#             (self.form_url % self.report.pk),
#             data={'0-key': self.report_key,
#                   'wizard_goto_step':1,
#                   'form_wizard' + str(self.report.id) + '-current_step': 0},
#             follow=True
#         )
#
#     def test_edit_record_page_renders_key_prompt(self):
#         response = self.client.get(self.form_url % self.report.pk, follow=True)
#         self.assertTemplateUsed(response, 'decrypt_record_for_edit.html')
#         self.assertIsInstance(response.context['form'], SecretKeyForm)
#
#     def test_edit_form_advances_to_second_page(self):
#         response = self.enter_edit_key()
#         self.assertTemplateUsed(response, 'form.html')
#         self.assertIsInstance(response.context['form'], QuestionPageForm)
#         self.assertContains(response, 'name="1-question_%i"' % self.question1.pk)
#         self.assertNotContains(response, 'name="1-question_%i"' % self.question2.pk)
#
#     def test_initial_is_passed_to_forms(self):
#         response = self.enter_edit_key()
#         form = response.context['form']
#         self.assertIn('test answer', form.initial.values())
#         self.assertIn('another answer to a different question', form.initial.values())
#
#     def edit_record(self, record_to_edit):
#         wizard = EncryptedBaseWizard.wizard_factory([self.page1, self.page2], object_to_edit=record_to_edit)()
#
#         KeyForm1 = wizard.form_list[0]
#         PageOneForm = wizard.form_list[1]
#         PageTwoForm = wizard.form_list[2]
#         KeyForm2 = wizard.form_list[3]
#
#         key_form_1 = KeyForm1({'key': self.report_key})
#         key_form_1.is_valid()
#
#         page_one = PageOneForm({'question_%i' % self.question1.pk: 'test answer'})
#         page_one.is_valid()
#         page_two = PageTwoForm({'question_%i' % self.question2.pk: 'edited answer to second question',})
#         page_two.is_valid()
#         key_form_2 = KeyForm2({'key': self.report_key})
#         key_form_2.is_valid()
#
#         self._get_wizard_response(wizard, form_list=[key_form_1, page_one, page_two, key_form_2],
#         request = self.request)
#
#     def test_edit_modifies_record(self):
#         self.maxDiff = None
#
#         json_report = """[
#     { "answer": "test answer",
#       "id": %i,
#       "section": 1,
#       "question_text": "first question",
#       "type": "SingleLineText"
#     },
#     { "answer": "edited answer to second question",
#       "id": %i,
#       "section": 1,
#       "question_text": "2nd question",
#       "type": "SingleLineText"
#     }
#   ]"""  % (self.question1.pk, self.question2.pk)
#
#         self.edit_record(self.report)
#         self.assertEqual(Report.objects.count(), 1)
#         self.assertEqual(sort_json(Report.objects.get(id=self.report.pk).decrypted_report(self.report_key)),
#                          sort_json(json_report))
#
#     def test_cant_edit_with_bad_key(self):
#         self.maxDiff = None
#
#         wizard = EncryptedBaseWizard.wizard_factory([self.page1, self.page2], object_to_edit=self.report)()
#
#         KeyForm1 = wizard.form_list[0]
#
#         key_form_1 = KeyForm1({'key': "not the right key!!!"})
#         self.assertFalse(key_form_1.is_valid())
#
#     def test_cant_save_edit_with_bad_key(self):
#         wizard = EncryptedBaseWizard.wizard_factory([self.page1, self.page2], object_to_edit=self.report)()
#
#         KeyForm1 = wizard.form_list[0]
#         PageOneForm = wizard.form_list[1]
#         PageTwoForm = wizard.form_list[2]
#         KeyForm2 = wizard.form_list[3]
#
#         key_form_1 = KeyForm1({'key': self.report_key})
#         key_form_1.is_valid()
#
#         page_one = PageOneForm({'question_%i' % self.question1.pk: 'test answer'})
#         page_one.is_valid()
#         page_two = PageTwoForm({'question_%i' % self.question2.pk: 'edited answer to second question',})
#         page_two.is_valid()
#         key_form_2 = KeyForm2({'key': "not the right key"})
#         self.assertFalse(key_form_2.is_valid())
#         with self.assertRaises(KeyError):
#             self._get_wizard_response(wizard, form_list=[key_form_1, page_one, page_two, key_form_2],
#               request = self.request)
#         self.assertEqual(sort_json(Report.objects.get(id=self.report.pk).decrypted_report(self.report_key)),
#                          sort_json(self.report_text))
#
#     def test_edit_saves_anonymous_row(self):
#         self.edit_record(self.report)
#         self.assertEqual(EvalRow.objects.count(), 2)
#         self.assertEqual(EvalRow.objects.last().action, EvalRow.EDIT)
#         self.edit_record(self.report)
#         self.assertEqual(EvalRow.objects.count(), 3)
#         self.assertEqual(Report.objects.count(), 1)
#
#     def test_edit_saves_original_record_if_no_data_exists(self):
#         old_report = Report(owner = self.request.user)
#         old_report.encrypt_report(self.report_text, self.report_key)
#         old_report.save()
#
#         self.assertEqual(EvalRow.objects.count(), 1)
#         self.assertEqual(EvalRow.objects.filter(action=EvalRow.FIRST).count(), 0)
#
#         self.edit_record(record_to_edit=old_report)
#         self.assertEqual(EvalRow.objects.count(), 3)
#         self.assertEqual(EvalRow.objects.filter(action=EvalRow.FIRST).count(), 1)
#         self.assertEqual(EvalRow.objects.last().action, EvalRow.EDIT)
#         self.assertEqual(EvalRow.objects.filter(action=EvalRow.FIRST).first().record_identifier,
#               EvalRow.objects.last().record_identifier)
#         self.assertNotEqual(EvalRow.objects.filter(action=EvalRow.FIRST).first().row, EvalRow.objects.last().row)
#
#
