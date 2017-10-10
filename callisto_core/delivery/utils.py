from .view_helpers import EncryptedReportStorageHelper


class RecordDataUtil(object):

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
        self.data = EncryptedReportStorageHelper.empty_storage()
        return self.data
