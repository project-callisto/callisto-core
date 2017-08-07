import json

from django import forms
from django.test import TestCase

from ..models import (
    Checkbox, Choice, Page, RadioButton, SingleLineText,
)


class PageTest1(TestCase):

    def test_page_can_have_position(self):
        Page.objects.create()
        page = Page.objects.create(position=10)
        self.assertEqual(Page.objects.get(pk=page.pk).position, 10)

    def test_page_position_defaults_to_last(self):
        pages = 7
        for i in range(pages):
            Page.objects.create()
        last_page = Page.objects.create()
        self.assertEqual(last_page.position, pages + 1)

    def test_page_can_have_section(self):
        when_page = Page.objects.create()
        who_page = Page.objects.create(section=Page.WHO)
        self.assertEqual(Page.objects.get(pk=who_page.pk).section, Page.WHO)
        self.assertEqual(Page.objects.get(pk=when_page.pk).section, Page.WHEN)

    def test_page_can_have_multiple(self):
        single_page = Page.objects.create()
        multiple_page = Page.objects.create(
            multiple=True, name_for_multiple="random field")
        self.assertFalse(Page.objects.get(pk=single_page.pk).multiple)
        self.assertTrue(Page.objects.get(pk=multiple_page.pk).multiple)
        self.assertTrue(
            Page.objects.get(
                pk=multiple_page.pk).name_for_multiple,
            "random field")

    def test_page_infobox_can_be_specified(self):
        Page.objects.create(infobox="More information")
        self.assertEqual(Page.objects.last().infobox, "More information")

    def test_position_not_overriden_on_save(self):
        page = Page.objects.create()
        starting_position = page.position
        Page.objects.create()
        page.save()
        self.assertEqual(starting_position, page.position)


class ItemTestCase(TestCase):

    def setUp(self):
        self.page = Page.objects.create()


class FormQuestionModelTest(ItemTestCase):

    def test_questions_have_text(self):
        SingleLineText.objects.create(text="This is a question")
        self.assertEqual(SingleLineText.objects.count(), 1)
        self.assertEqual(
            SingleLineText.objects.first().text,
            "This is a question")

    def test_string_representation(self):
        question = SingleLineText.objects.create(text="What's up?")
        self.assertEqual(str(question), "What's up? (Type: SingleLineText)")

    def test_questions_can_have_pages(self):
        page = Page.objects.create()
        SingleLineText.objects.create(
            text="This is a question on page 4", page=page)
        self.assertEqual(SingleLineText.objects.first().page, page)

    def test_questions_have_pages_by_default(self):
        SingleLineText.objects.create(text="This is a question with no page")
        self.assertEqual(SingleLineText.objects.first().page.position, 1)

    def test_questions_get_added_to_end_by_default(self):
        # setup creates one page
        pages = 9
        for i in range(pages):
            Page.objects.create()
        question = SingleLineText.objects.create(
            text="This is a question with no page")
        self.assertEqual(question.page.position, pages + 1)

    def test_questions_can_have_descriptive_text(self):
        SingleLineText.objects.create(
            text="This is a question",
            descriptive_text="You might answer it so")
        self.assertEqual(
            SingleLineText.objects.first().descriptive_text,
            "You might answer it so")

    def test_questions_have_position(self):
        SingleLineText.objects.create(text="some question")
        self.assertEqual(SingleLineText.objects.first().position, 0)

    def test_question_position_can_be_specified(self):
        SingleLineText.objects.create(text="some question", position=10)
        self.assertEqual(SingleLineText.objects.first().position, 10)


class SingleLineTextModelTestCase(ItemTestCase):

    def test_make_field_applies_css(self):
        question = SingleLineText.objects.create(
            text="This is a question with css").make_field()
        self.assertIn('form-control input-lg', question.widget.attrs['class'])

    def test_make_field_works_without_placeholder(self):
        question = SingleLineText.objects.create(
            text="This is a question without placeholder").make_field()
        self.assertEqual(None, question.widget.attrs.get('placeholder'))

    def test_serializes_correctly(self):
        question = SingleLineText.objects.create(
            text="This is a question to be answered")
        serialized_q = question.serialize_for_report("my answer")
        json_report = json.loads("""
    { "answer": "my answer",
      "id": %i,
      "section": 1,
      "question_text": "This is a question to be answered",
      "type": "SingleLineText"
    }""" % question.pk)
        self.assertEqual(serialized_q, json_report)

    def test_serializes_no_answer_correctly(self):
        question = SingleLineText.objects.create(
            text="This is a question to be answered")
        serialized_q = question.serialize_for_report()
        json_report = json.loads("""
    { "answer": "",
      "id": %i,
      "section": 1,
      "question_text": "This is a question to be answered",
      "type": "SingleLineText"
    }""" % question.pk)
        self.assertEqual(serialized_q, json_report)


class RadioButtonTestCase(ItemTestCase):

    def setUp(self):
        super(RadioButtonTestCase, self).setUp()
        self.question = RadioButton.objects.create(
            text="this is a radio button question")
        for i in range(5):
            Choice.objects.create(
                text="This is choice %i" %
                i, question=self.question)

    def test_can_retrieve_choices(self):
        self.assertEqual(self.question.choice_set.count(), 5)
        self.assertEqual(
            self.question.choice_set.first().text,
            "This is choice 0")

    def test_generates_radio_button(self):
        self.assertEqual(len(self.question.make_field().choices), 5)
        self.assertEqual(
            self.question.make_field().choices[4][1],
            "This is choice 4")
        self.assertIsInstance(
            self.question.make_field().widget,
            forms.RadioSelect)

    def test_can_make_dropdown(self):
        dropdown = RadioButton.objects.create(
            text="this is a dropdown question", is_dropdown=True)
        for i in range(5):
            Choice.objects.create(
                text="This is choice %i" %
                i, question=dropdown)
        self.assertEqual(len(dropdown.make_field().choices), 5)
        self.assertEqual(
            dropdown.make_field().choices[3][1],
            "This is choice 3")
        self.assertIsInstance(dropdown.make_field().widget, forms.Select)

    def test_serializes_correctly(self):
        object_ids = [choice.pk for choice in self.question.choice_set.all()]
        serialized_q = self.question.serialize_for_report(object_ids[3])
        selected_id = object_ids[3]
        object_ids.insert(0, self.question.pk)
        object_ids.insert(0, selected_id)
        json_report = json.loads("""
    { "answer": %i,
      "id": %i,
      "question_text": "this is a radio button question",
      "section": 1,
      "choices": [{"id": %i, "choice_text": "This is choice 0"},
                  {"id": %i, "choice_text": "This is choice 1"},
                  {"id": %i, "choice_text": "This is choice 2"},
                  {"id": %i, "choice_text": "This is choice 3"},
                  {"id": %i, "choice_text": "This is choice 4"}],
      "type": "RadioButton"
    }""" % tuple(object_ids))
        self.assertEqual(serialized_q, json_report)


class CheckboxTestCase(ItemTestCase):

    def setUp(self):
        self.page = Page.objects.create()
        self.question = Checkbox.objects.create(
            text="this is a checkbox question")
        for i in range(5):
            Choice.objects.create(
                text="This is choice %i" %
                i, question=self.question)

    def test_can_retrieve_choices(self):
        self.assertEqual(self.question.choice_set.count(), 5)
        self.assertEqual(
            self.question.choice_set.first().text,
            "This is choice 0")

    def test_generates_checkbox(self):
        self.assertEqual(len(self.question.make_field().choices), 5)
        self.assertEqual(
            self.question.make_field().choices[4][1],
            "This is choice 4")
        self.assertIsInstance(
            self.question.make_field().widget,
            forms.CheckboxSelectMultiple)

    def test_serializes_correctly(self):
        self.maxDiff = None
        object_ids = [choice.pk for choice in self.question.choice_set.all()]
        selected_id_1 = object_ids[3]
        selected_id_2 = object_ids[1]
        serialized_q = self.question.serialize_for_report(
            [selected_id_1, selected_id_2])
        object_ids.insert(0, self.question.pk)
        object_ids.insert(0, selected_id_2)
        object_ids.insert(0, selected_id_1)
        json_report = json.loads("""
    { "answer": [%i, %i],
      "id": %i,
      "question_text": "this is a checkbox question",
      "section": 1,
      "choices": [{"id": %i, "choice_text": "This is choice 0"},
                  {"id": %i, "choice_text": "This is choice 1"},
                  {"id": %i, "choice_text": "This is choice 2"},
                  {"id": %i, "choice_text": "This is choice 3"},
                  {"id": %i, "choice_text": "This is choice 4"}],
      "type": "Checkbox"
    }""" % tuple(object_ids))
        self.assertEqual(serialized_q, json_report)


class PageTest2(TestCase):

    def test_can_save_infobox(self):
        page_id = Page.objects.create(infobox="you'll be asked later").pk
        self.assertEqual(
            Page.objects.get(
                pk=page_id).infobox,
            "you'll be asked later")
