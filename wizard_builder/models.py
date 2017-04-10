import copy

from polymorphic.models import PolymorphicModel

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.safestring import mark_safe
from django.contrib.sites.models import Site

from .managers import PageBaseQuerySet


def get_page_position():
    try:
        return PageBase.objects.latest('position').position + 1
    except ObjectDoesNotExist:
        return 0


def get_current_site_wrapper():
    try:
        return str(Site.objects.get_current().id)
    except ImproperlyConfigured:
        return None


class PageBase(PolymorphicModel):
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

    position = models.PositiveSmallIntegerField("position", default=get_page_position)
    section = models.IntegerField(choices=SECTION_CHOICES, default=WHEN)
    site = models.ForeignKey(Site, default=get_current_site_wrapper)
    objects = PageBaseQuerySet.as_manager()

    class Meta:
        ordering = ['position']
        verbose_name = 'Form page'


class TextPage(PageBase):
    title = models.TextField(blank=True)
    text = models.TextField(blank=False)

    def __str__(self):
        if len(self.title.strip()) > 0:
            return "Page %i (%s)" % (self.position, self.title)
        else:
            return "Page %i (%s)" % (self.position, self.text[:97] + '...')


class QuestionPage(PageBase):
    encouragement = models.TextField(blank=True)
    infobox = models.TextField(blank=True,
                               verbose_name='why is this asked? wrap additional titles in [[double brackets]]')
    multiple = models.BooleanField(blank=False, default=False,
                                   verbose_name='User can add multiple')
    name_for_multiple = models.TextField(blank=True, verbose_name='name of field for "add another" prompt')

    def __str__(self):
        questions = self.formquestion_set.order_by('position')
        if len(questions) > 0:
            return "Page %i (%s)" % (self.position, questions[0].text)
        else:
            return "Page %i" % self.position

    class Meta:
        ordering = ['position']


def get_page():
    try:
        return QuestionPage.objects.latest('position').pk
    except ObjectDoesNotExist:
        return None


class FormQuestion(PolymorphicModel):
    text = models.TextField(blank=False)

    page = models.ForeignKey('QuestionPage', editable=True, default=get_page, blank=True)
    position = models.PositiveSmallIntegerField("position", default=0)
    descriptive_text = models.TextField(blank=True)

    added = models.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        super(FormQuestion, self).__init__(*args, **kwargs)
        self.section = self.page.section

    def __str__(self):
        return self.text + " (" + str(type(self).__name__) + ")"

    def clone(self):
        return copy.deepcopy(self)

    def get_extras(self):
        return None

    def get_label(self):
        return mark_safe(self.text)

    class Meta:
        ordering = ['position']
        verbose_name = 'question'


class SingleLineText(FormQuestion):

    def make_field(self):
        return forms.CharField(
            label=self.get_label(),
            required=False,
            widget=forms.TextInput(
                attrs={
                    'class': "form-control input-lg",
                },
            ),
        )

    def serialize_for_report(self, answer="", *args):
        return {'id': self.pk, 'question_text': self.text, 'answer': answer,
                'type': 'SingleLineText', 'section': self.section}


class SingleLineTextWithMap(FormQuestion):
    map_link = models.CharField(blank=False, max_length=500)

    def make_field(self):
        link_to_map = """<a href='{0}' target='_blank' class="map_link">
                          <img alt="Map of campus" src="/static/images/map_icon.png" />
                      </a>""".format(self.map_link)
        return forms.CharField(
            label=self.get_label(),
            help_text=mark_safe(link_to_map),
            required=False,
            widget=forms.TextInput(
                attrs={
                    'class': "form-control input-lg map-field",
                },
            ),
        )

    def serialize_for_report(self, answer="", *args):
        return {'id': self.pk, 'question_text': self.text, 'answer': answer,
                'type': 'SingleLineText', 'section': self.section}


class MultiLineText(FormQuestion):

    def make_field(self):
        return forms.CharField(
            label=self.get_label(),
            required=False,
            widget=forms.Textarea(
                attrs={
                    'class': "form-control",
                    'max_length': 30000,
                },
            ),
        )

    def serialize_for_report(self, answer="", *args):
        return {'id': self.pk, 'question_text': self.text, 'answer': answer,
                'type': 'MultiLineText', 'section': self.section}


class MultipleChoice(FormQuestion):
    cached_choices = None

    def clone(self):
        question_copy = copy.deepcopy(self)
        # copy choices
        choices = [copy.deepcopy(choice) for choice in self.choice_set.all()]
        question_copy.cached_choices = choices
        return question_copy

    def get_choices(self):
        if self.cached_choices:
            return self.cached_choices
        else:
            choices = [copy.deepcopy(choice) for choice in self.choice_set.all()]
            self.cached_choices = choices
            return choices

    def serialize_choices(self):
        return [{"id": choice.pk, "choice_text": choice.text} for choice in self.get_choices()]


class Checkbox(MultipleChoice):

    def make_field(self):
        choices = self.get_choices()
        choice_tuples = [(choice.pk, choice.make_choice()) for choice in choices]
        return forms.MultipleChoiceField(choices=choice_tuples,
                                         label=self.text,
                                         required=False,
                                         widget=forms.CheckboxSelectMultiple)

    def serialize_for_report(self, answer, *args):
        result = {'id': self.pk, 'question_text': self.text, 'choices': self.serialize_choices(),
                  'answer': answer, 'type': 'Checkbox', 'section': self.section}
        if len(args) > 0 and args[0]:
            result['extra'] = args[0]
        return result


class RadioButton(MultipleChoice):
    is_dropdown = models.BooleanField(default=False)

    def make_field(self):
        choices = self.get_choices()
        choice_tuples = [(choice.pk, choice.make_choice()) for choice in choices]
        return forms.ChoiceField(choices=choice_tuples,
                                 label=self.text,
                                 required=False,
                                 widget=forms.Select(attrs={'class': "form-control input-lg"}) if self.is_dropdown else
                                 forms.RadioSelect)

    def serialize_for_report(self, answer, *args):
        result = {'id': self.pk, 'question_text': self.text, 'choices': self.serialize_choices(),
                  'answer': answer, 'type': 'RadioButton', 'section': self.section}
        if len(args) > 0 and args[0]:
            result['extra'] = args[0]
        return result

    def get_extras(self):
        choices = self.cached_choices or self.choice_set.all()
        return [("question_%s_extra-%s" % (self.pk, choice.pk),
                 choice.extra_info_placeholder) for choice in choices if choice.extra_info_placeholder]


class Choice(models.Model):
    question = models.ForeignKey('MultipleChoice')
    text = models.TextField(blank=False)
    position = models.PositiveSmallIntegerField("Position", default=0)
    extra_info_placeholder = models.CharField(blank=True, max_length=500,
                                              verbose_name='Placeholder for extra info field (leave blank for no '
                                              'field)')

    def make_choice(self):
        return self.text

    class Meta:
        ordering = ['position', 'pk']


class Date(FormQuestion):

    def make_field(self):
        return forms.CharField(
            label=self.get_label(),
            required=False,
            widget=forms.TextInput(
                attrs={
                    'class': "form-control input-lg date-field",
                },
            ),
        )

    def serialize_for_report(self, answer, *args):
        return {'id': self.pk, 'question_text': self.text, 'answer': answer,
                'type': 'Date', 'section': self.section}


class Conditional(models.Model):
    EXACTLY = "and"
    IN = "or"

    OPTIONS = (
        (EXACTLY, 'exactly'),
        (IN, 'in'),
    )
    condition_type = models.CharField(max_length=50,
                                      choices=OPTIONS,
                                      default=EXACTLY)

    page = models.OneToOneField(PageBase)
    question = models.ForeignKey(FormQuestion)
    answer = models.CharField(max_length=150)

    def __str__(self):
        return "Conditional for " + str(self.page)
