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
        # print('_parse_old_data')
        self._create_page_arrays()
        for question in self.old_data:
            self._add_question_answer(question)
            self._add_question_form(question)

    def _create_page_arrays(self):
        # print('_create_page_arrays')
        page_array = []
        for _ in range(self._section_count()):
            page_array.append([])
        self.new_data[self.form_key] = page_array

    def _section_count(self):
        # print('_section_count')
        max_sections = 1
        for question in self.old_data:
            max_sections = max([max_sections, question.get('section', 0)])
        return max_sections

    def _add_question_answer(self, question: dict):
        print('_add_question_answer', question)
        pk = question.get('id')
        if pk:
            self.new_data[self.answer_key].update({
                f'question_{pk}': question.get('answer', '')
            })

    def _add_question_form(self, question: dict):
        if question.get('answers'):
            self._add_perp_questions(question)
        else:
            new_form = self._add_form_fields(question)
            self._add_form_to_pages(new_form)

    def _add_form_to_pages(self, form: dict):
        # print('_add_form_to_pages', form)
        section_index = form['section'] - 2
        self.new_data[self.form_key][section_index].append(form)

    def _add_form_fields(self, question: dict, extra={}) -> dict:
        # print('_add_form_fields', question, extra)
        new_form = {
            'section': question.get('section', 1),
            'type': question.get('type'),
            'id': question.get('id'),
            'question_text': '<p>{}</p>'.format(
                question.get('question_text', '')),
            'field_id': 'question_{}'.format(question.get('id')),
            **extra,
        }
        if question.get('choices'):
            new_form['choices'] = self._get_choices(question.get('choices'))
        return new_form

    def _add_perp_questions(self, question: dict) -> dict:
        prep_forms = question.get('answers', [])
        for index, perp_questions in enumerate(prep_forms):
            for question in perp_questions:
                question = self._uniquify_perp_question(question, index)
                self._add_question_answer(question)
                self._add_question_form(question)

    def _uniquify_perp_question(self, question: dict, index: int) -> dict:
        pk = str(question.get('id', 0))
        if not pk.startswith('perp_'):
            question['id'] = f'perp_{index}_{pk}'
        return question

    def _get_choices(self, choices: list) -> list:
        # print('_get_choices', choices)
        return [
            self._get_choice(choice)
            for choice in choices
        ]

    def _get_choice(self, choice: dict) -> dict:
        # print('_get_choice', choice)
        return {
            'extra_info_text': '',
            'options': [],
            'position': 0,
            'pk': choice.get('id'),
            'text': choice.get('choice_text'),
        }
