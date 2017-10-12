from .view_helpers import EncryptedReportStorageHelper


class RecordDataUtil(object):
    answer_key = EncryptedReportStorageHelper.storage_data_key
    form_key = EncryptedReportStorageHelper.storage_form_key

    @classmethod
    def data_is_old_format(cls, data: dict or list) -> bool:
        '''the old data top level object is a list'''
        return isinstance(data, list)

    @classmethod
    def transform_if_old_format(cls, data: dict or list) -> dict:
        '''transforms the data input, if its in the old format'''
        if cls.data_is_old_format(data):
            return cls.transform_data_to_new_format(data)
        else:
            return data

    @classmethod
    def transform_data_to_new_format(cls, data: list) -> dict:
        self = cls()
        self.old_data = data
        self.new_data = EncryptedReportStorageHelper.empty_storage()
        self._parse_old_data()
        return self.new_data

    def _parse_old_data(self):
        self._create_page_arrays()
        for question in self.old_data:
            self._add_question_answer(question)
            self._add_question_form(question)

    def _create_page_arrays(self):
        page_array = []
        for _ in range(self._section_count()):
            page_array.append([])
        self.new_data[self.form_key] = page_array

    def _section_count(self):
        max_sections = 1
        for question in self.old_data:
            max_sections = max([max_sections, question.get('section', 0)])
        return max_sections

    def _add_question_answer(self, question: dict):
        new_answer = self.new_data.get(self.answer_key, {})
        pk = question.get('id')
        new_answer[f'question_{pk}'] = question.get('answer', '')
        self.new_data[self.answer_key] = new_answer

    def _add_question_form(self, question: dict):
        new_form = {
            'section': question.get('section', 1),
            'type': question.get('type'),
            'id': question.get('id'),
            'question_text': '<p>{}</p>'.format(
                question.get('question_text', '')),
            'field_id': 'question_{}'.format(question.get('id')),
        }
        if question.get('choices'):
            new_form['choices'] = self._get_choices(question.get('choices'))
        section_index = new_form['section'] - 1
        self.new_data[self.form_key][section_index].append(new_form)

    def _get_choices(self, choices: list) -> list:
        return [
            self._get_choice(choice)
            for choice in choices
        ]

    def _get_choice(self, choice: dict) -> dict:
        return {
            'extra_info_text': '',
            'options': [],
            'position': 0,
            'pk': choice.get('id'),
            'text': choice.get('choice_text'),
        }
