from .page_admin import (
    PageBaseAdmin, QuestionPageAdmin, TextPageAdmin
)
from .question_admin import (
    FormQuestionAdmin
)
from ..models import (
    PageBase, QuestionPage, TextPage, Conditional
)


admin.site.register(FormQuestion, FormQuestionParentAdmin)

admin.site.register(PageBase, PageBaseAdmin)
admin.site.register(QuestionPage, QuestionPageAdmin)
admin.site.register(TextPage, TextPageAdmin)

admin.site.register(Conditional)
