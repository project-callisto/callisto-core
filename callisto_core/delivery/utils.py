class RecordDataUtil(object):

    @classmethod
    def data_is_old_format(cls, data):
        '''the old data top level object is a list'''
        return isinstance(data, list)

    @classmethod
    def transform(cls, data):
        if cls.data_is_old_format(data):
            return cls.transform_data_to_new_format(data)

    @classmethod
    def transform_data_to_new_format(cls, data):
        self = cls()
        self.data = data
        return self.data
