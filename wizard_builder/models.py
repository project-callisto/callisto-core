import copy

from django import forms
from django.contrib.sites.models import Site
from django.db import models
from django.utils.safestring import mark_safe

from .managers import FormQuestionManager, PageManager


class Page(models.Model):
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
    infobox = HTMLField(blank=True)
    multiple = models.BooleanField(
        blank=False,
        default=False,
        verbose_name='User can add multiple',
    )
    name_for_multiple = models.TextField(
        blank=True,
        verbose_name='name of field for "add another" prompt',
    )

    objects = PageManager()

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
            self.position = cls.objects.exclude(pk=self.pk).latest('position').position + 1

    class Meta:
        ordering = ['position']


# TODO: rename to Question when downcasting is removed
class FormQuestion(TimekeepingBase, models.Model):
    text = HTMLField(blank=False)
    descriptive_text = HTMLField(blank=True)
    page = models.ForeignKey(Page, editable=True, null=True, on_delete=models.SET_NULL)
    position = models.PositiveSmallIntegerField("position", default=0)
    descriptive_text = models.TextField(blank=True)
    added = models.DateTimeField(auto_now_add=True)
    objects = FormQuestionManager()

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

    def clone(self):
        return copy.deepcopy(self)

    def get_extras(self):
        return None

    def get_label(self):
        return mark_safe(self.text)

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
    objects = FormQuestionManager()

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
    question = models.ForeignKey('MultipleChoice', on_delete=models.CASCADE)
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
