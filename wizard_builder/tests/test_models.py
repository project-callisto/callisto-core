import json

from django import forms
from django.test import TestCase

from .. import mocks
from ..models import (
    Checkbox, Choice, ChoiceOption, FormQuestion, Page, RadioButton,
    SingleLineText,
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

    def test_question_text_serializes_correctly(self):
        question = FormQuestion.objects.create(
            text='This is a question to be answered',
        )
        serialized_q = question.serialized
        self.assertEqual(
            serialized_q['question_text'],
            question.text,
        )

    def test_questions_have_position(self):
        SingleLineText.objects.create(text="some question")
        self.assertEqual(SingleLineText.objects.first().position, 0)

    def test_question_position_can_be_specified(self):
        SingleLineText.objects.create(text="some question", position=10)
        self.assertEqual(SingleLineText.objects.first().position, 10)


class SingleLineTextModelTestCase(ItemTestCase):

    def test_question_text_serializes_correctly(self):
        question = FormQuestion.objects.create(
            text='This is a question to be answered',
        )
        serialized_q = question.serialized
        self.assertEqual(
            serialized_q['question_text'],
            question.text,
        )


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
        field = mocks.MockQuestion(self.question.serialized).make_field()
        self.assertEqual(len(field.choices), 5)
        self.assertEqual(field.choices[4][1], "This is choice 4")
        self.assertIsInstance(field.widget, forms.RadioSelect)

    def test_can_make_dropdown(self):
        model = RadioButton.objects.create(
            text="this is a dropdown question", is_dropdown=True)
        for i in range(5):
            Choice.objects.create(text=f"choice {i}", question=model)
        mock = mocks.MockQuestion(model.serialized)
        field = mock.make_field()
        self.assertEqual(len(field.choices), 5)
        self.assertEqual(field.choices[3][1], "choice 3")
        self.assertIsInstance(field.widget, forms.Select)

    def test_choices_serialized(self):
        object_ids = [choice.pk for choice in self.question.choice_set.all()]
        serialized_q = self.question.serialized
        self.assertEqual(type(serialized_q['choices']), list)
        self.assertTrue(len(serialized_q['choices']))

    def test_choice_extra_info_serialized(self):
        choice = self.question.choices[0]
        choice.extra_info_text = 'cats are good'
        choice.save()
        serialized_q = self.question.serialized
        self.assertIn('extra_info_text', str(serialized_q))
        self.assertIn('cats are good', str(serialized_q))

    def test_choice_extra_dropdown_serialized(self):
        choice = self.question.choices[0]
        ChoiceOption.objects.create(
            text='lizards are cool',
            choice=choice,
        )
        ChoiceOption.objects.create(
            text='birds can skateboard',
            choice=choice,
        )
        serialized_q = self.question.serialized
        self.assertIn('options', str(serialized_q))
        self.assertIn('lizards are cool', str(serialized_q))
        self.assertIn('birds can skateboard', str(serialized_q))


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
        field = mocks.MockQuestion(self.question.serialized).make_field()
        self.assertEqual(len(field.choices), 5)
        self.assertEqual(field.choices[4][1], "This is choice 4")
        self.assertIsInstance(field.widget, forms.CheckboxSelectMultiple)
