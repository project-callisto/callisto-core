from . import fields


class MockPage(object):
    pk = None

    def __init__(self, data):
        self.section = data[0].get('section', 1)
        self.questions = self._create_questions(data)

    def _create_questions(self, data):
        questions = []
        for question_data in data:
            question = MockQuestion(question_data)
            questions.append(question)
        return questions


class MockQuestion(object):

    def __init__(self, data):
        self.id = data.get('id')
        self.text = data.get('question_text')
        self.type = data.get('type')
        self.section = data.get('section')
        # TODO: choices

    @property
    def field_id(self):
        return 'question_' + str(self.id)

    def make_field(self):
        field_generator = getattr(
            fields.QuestionField,  # from the QuestionFields object
            self.type.lower(),  # get the field that correspond to the question type
            QuestionFields.singlelinetext,  # otherwise get a singlelinetext field
        )
        return field_generator(self)
