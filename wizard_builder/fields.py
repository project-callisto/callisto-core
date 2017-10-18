from django import forms
from django.utils.safestring import mark_safe


class QuestionField(object):

    @classmethod
    def singlelinetext(cls, question):
        return forms.CharField(
            label=mark_safe(question.text),
            required=False,
        )

    @classmethod
    def textarea(cls, question):
        return forms.CharField(
            widget=forms.Textarea,
            label=mark_safe(question.text),
            required=False,
        )

    @classmethod
    def checkbox(cls, question):
        pass

    @classmethod
    def radiobutton(cls, question):
        pass
