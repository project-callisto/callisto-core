from .base import DowncastedAdmin, ChoiceInline


class SingleLineTextAdmin(DowncastedAdmin):
    base_model = SingleLineText


class MultiLineTextAdmin(DowncastedAdmin):
    base_model = MultiLineText


class SingleLineTextWithMapAdmin(DowncastedAdmin):
    base_model = MultiLineText


class RadioButtonAdmin(DowncastedAdmin):
    base_model = RadioButton
    inlines = [
        ChoiceInline,
    ]


class CheckboxAdmin(DowncastedAdmin):
    base_model = Checkbox
    inlines = [
        ChoiceInline,
    ]


class DateAdmin(DowncastedAdmin):
    base_model = Date


class FormQuestionAdmin(DowncastedAdmin):
    base_model = FormQuestion
    child_models = (
        (SingleLineText, SingleLineTextAdmin),
        (SingleLineTextWithMap, SingleLineTextWithMapAdmin),
        (MultiLineText, MultiLineTextAdmin),
        (RadioButton, RadioButtonAdmin),
        (Date, DateAdmin),
        (Checkbox, CheckboxAdmin)
    )
