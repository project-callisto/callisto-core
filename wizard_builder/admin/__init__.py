from django.contrib import admin

from ..models import (
    Checkbox, Date, FormQuestion, MultiLineText, MultipleChoice, PageBase,
    QuestionPage, RadioButton, SingleLineText, SingleLineTextWithMap, TextPage,
)
from .page_admin import PageBaseAdmin, PageBaseChildAdmin, QuestionPageAdmin
from .question_admin import (
    FormQuestionChildAdmin, FormQuestionParentAdmin, MultipleChoiceChildAdmin,
    MultipleChoiceParentAdmin,
)

admin.site.register(PageBase, PageBaseAdmin)
admin.site.register(QuestionPage, QuestionPageAdmin)
admin.site.register(TextPage, PageBaseChildAdmin)

admin.site.register(FormQuestion, FormQuestionParentAdmin)
admin.site.register(SingleLineText, FormQuestionChildAdmin)
admin.site.register(SingleLineTextWithMap, FormQuestionChildAdmin)
admin.site.register(MultiLineText, FormQuestionChildAdmin)
admin.site.register(Date, FormQuestionChildAdmin)

admin.site.register(MultipleChoice, MultipleChoiceParentAdmin)
admin.site.register(Checkbox, MultipleChoiceChildAdmin)
admin.site.register(RadioButton, MultipleChoiceChildAdmin)
