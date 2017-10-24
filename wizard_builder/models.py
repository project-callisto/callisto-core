import logging

from django.contrib.sites.models import Site
from django.db import models
from django.forms.models import model_to_dict

from . import managers, model_helpers, fields

logger = logging.getLogger(__name__)


class Page(
    model_helpers.SerializedQuestionMixin,
    models.Model,
):
    WHEN = 1
    WHERE = 2
    WHAT = 3
    WHO = 4
    SECTION_CHOICES = (
        (WHEN, 'When'),
        (WHERE, 'Where'),
        (WHAT, 'What'),
        (WHO, 'Who'),
    )
    position = models.PositiveSmallIntegerField("position", default=0)
    section = models.IntegerField(choices=SECTION_CHOICES, default=WHEN)
    sites = models.ManyToManyField(Site)

    objects = managers.PageManager()

    def __str__(self):
        questions = self.formquestion_set.order_by('position')
        if len(questions) > 0 and self.site_names:
            question_str = "(Question 1: {})".format(questions[0].text)
            site_str = "(Sites: {})".format(self.site_names)
            return "{} {} {}".format(self.short_str, question_str, site_str)
        elif len(questions) > 0:
            question_str = "(Question 1: {})".format(questions[0].text)
            return "{} {}".format(self.short_str, question_str)
        else:
            return "{}".format(self.short_str)

    @property
    def short_str(self):
        return "Page {}".format(self.position)

    @property
    def site_names(self):
        return [site.name for site in self.sites.all()]

    @property
    def questions(self):
        return list(self.formquestion_set.order_by('position'))

    def save(self, *args, **kwargs):
        self.set_page_position()
        super().save(*args, **kwargs)

    def set_page_position(self):
        '''
            Page.position defaults to 0, but we take 0 to mean "not set"
            so when there are no pages, Page.position is set to 1

            otherwise we Page.position to the position of the latest
            object that isn't self, +1
        '''
        cls = self.__class__
        if cls.objects.count() == 0:
            self.position = 1
        elif bool(cls.objects.exclude(pk=self.pk)) and not self.position:
            self.position = cls.objects.exclude(
                pk=self.pk).latest('position').position + 1

    class Meta:
        ordering = ['position']


# TODO: rename to Question when downcasting is removed
class FormQuestion(models.Model):
    text = models.TextField(blank=True)
    descriptive_text = models.TextField(blank=True)
    page = models.ForeignKey(
        Page,
        editable=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    position = models.PositiveSmallIntegerField("position", default=0)
    objects = managers.FormQuestionManager()
    type = models.TextField(
        choices=fields.get_field_options(),
        blank=False,
        null=True)

    def __str__(self):
        type_str = "(Type: {})".format(str(type(self).__name__))
        if self.site_names:
            site_str = "(Sites: {})".format(self.site_names)
            return "{} {} {}".format(self.short_str, type_str, site_str)
        else:
            return "{} {}".format(self.short_str, type_str)

    @property
    def field_id(self):
        return "question_{}".format(self.pk)

    @property
    def short_str(self):
        return self.text

    @property
    def site_names(self):
        if self.page:
            return self.page.site_names
        else:
            return None

    @property
    def section(self):
        if self.page:
            return self.page.section
        else:
            return None

    @property
    def serialized(self):
        data = model_to_dict(self)
        data.update({
            'question_text': self.text,
            'type': self._meta.model_name.capitalize(),
            'field_id': self.field_id,
        })
        return data

    def set_question_page(self):
        if not self.page:
            self.page = Page.objects.latest('position')

    def save(self, *args, **kwargs):
        self.set_question_page()
        super(FormQuestion, self).save(*args, **kwargs)

    class Meta:
        ordering = ['position']
        verbose_name = 'question'


class SingleLineText(FormQuestion):
    pass


class TextArea(FormQuestion):
    pass


class MultipleChoice(FormQuestion):
    objects = managers.FormQuestionManager()

    @property
    def serialized(self):
        data = super().serialized
        data.update({'choices': self.serialized_choices})
        return data

    @property
    def serialized_choices(self):
        return [choice.data for choice in self.choices]

    @property
    def choices(self):
        return list(self.choice_set.all().order_by('position'))


class Checkbox(MultipleChoice):

    class Meta:
        verbose_name_plural = "checkboxes"


class RadioButton(MultipleChoice):
    is_dropdown = models.BooleanField(default=False)


class Choice(models.Model):
    question = models.ForeignKey(MultipleChoice, on_delete=models.CASCADE)
    text = models.TextField(blank=False)
    position = models.PositiveSmallIntegerField("Position", default=0)
    extra_info_text = models.TextField(blank=True)

    @property
    def data(self):
        return {
            'pk': self.pk,
            'text': self.text,
            'options': self.options_data,
            'position': self.position,
            'extra_info_text': self.extra_info_text,
        }

    @property
    def options_data(self):
        return [
            {'pk': option.pk, 'text': option.text}
            for option in self.options
        ]

    @property
    def options(self):
        return list(self.choiceoption_set.all())

    class Meta:
        ordering = ['position', 'pk']


class ChoiceOption(models.Model):
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
    text = models.TextField(blank=False)
