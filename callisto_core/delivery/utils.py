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
        for question in self.old_data:
            self._set_question_answer(question)
            self._set_question_form(question)

    def _set_question_answer(self, question: dict):
        new_answer = self.new_data.get(self.answer_key)
        pk = question.get('id')
        new_answer[f'question_{pk}'] = question.get('answer')
        self.new_data[self.answer_key] = new_answer

    def _set_question_form(self, question: dict):
        pass
