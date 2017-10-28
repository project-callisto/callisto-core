from django.contrib import admin

from ..models import FormQuestion, Page
from .page_admin import PageAdmin
from .question_admin import FormQuestionAdmin

admin.site.register(Page, PageAdmin)
admin.site.register(FormQuestion, FormQuestionAdmin)
