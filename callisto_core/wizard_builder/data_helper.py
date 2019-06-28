from . import widgets


def resolve_list(item):
    return item[0] if is_single_element_list(item) else item


def is_single_element_list(item):
    return bool(isinstance(item, list)) and (len(item) == 1)


def is_unselected_list(answer):
    return len(answer) == 0


def is_empty_text_box(answer):
    return len(answer) == 1 and not answer[0]


def get_by_pk(items, pk):
    for item in items:
        if str(item.get("pk")) == str(resolve_list(pk)):
            return item
    else:
        return {}


class SerializedDataHelper(object):
    question_id_error_message = "field_id={} not found in {}"
    choice_id_error_message = "Choice(pk={}) not found in {}"
    not_answered_text = "[ Not Answered ]"

    @classmethod
    def get_zipped_data(cls, data={}, forms={}):
        self = cls()
        self.data = data
        self.zipped_data = []
        self._parse_forms(forms)
        return self.zipped_data

    def _parse_forms(self, forms):
        for form in forms:
            self._parse_questions(form)

    def _parse_questions(self, form):
        for question in form:
            answer = self._get_question_answer(question)
            self._parse_answers(question, answer)

    def _parse_answers(self, question, answer):
        if question.get("choices"):
            self._append_list_answers(answer, question)
        else:
            self._append_text_answer(answer, question)

    def _get_question_answer(self, question):
        return self.data.get(question.get("field_id"), "")

    def _append_text_answer(self, answer, question):
        self._append_answer(question, [answer])

    def _append_list_answers(self, answers, question):
        if not isinstance(answers, list):
            answers = [answers]
        choice_list = [self._get_choice_text(answer, question) for answer in answers]
        self._append_answer(question, choice_list)

    def _append_answer(self, question, answer):
        if is_empty_text_box(answer) or is_unselected_list(answer):
            answer = [self.not_answered_text]
        self.zipped_data.append({question["question_text"]: answer})

    def _get_choice_text(self, answer, question):
        choice = self._get_choice(question, answer)
        choice_text = choice.get("text")
        conditional_text = self._get_conditional_answer(choice, answer)
        if conditional_text:
            choice_text += ": " + conditional_text
        return choice_text

    def _get_choice(self, question, answer):
        return get_by_pk(question.get("choices", []), answer)

    def _get_conditional_answer(self, choice, answer):
        conditional_id = widgets.conditional_id(choice)
        if choice.get("extra_info_text"):
            return self.data.get(conditional_id, "")
        elif choice.get("options"):
            option_pk = self.data.get(conditional_id, "")
            option = get_by_pk(choice.get("options", []), option_pk)
            return option.get("text")
