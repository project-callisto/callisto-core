class SerializedQuestionMixin:

    @property
    def serialized_questions(self):
        return [
            question.serialized
            for question in self.questions
        ]
