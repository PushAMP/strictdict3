"""
Simplifiers are serializers of sort: they transform (.serialize()) objects to
simpler format understood by undelying storage engine (ints, strings and
dicts mostly) and transform them back (.deserialize()) to python objects, but
perform no checks, so input is supposed to be valid
"""
import datetime as dt
import decimal


class NullSimplifier(object):
    @staticmethod
    def serialize(data):
        return data

    @staticmethod
    def deserialize(data_str):
        return data_str


class DecimalSimplifier(object):
    @staticmethod
    def serialize(data):
        return str(data)

    @staticmethod
    def deserialize(data_str):
        return decimal.Decimal(data_str)


def view_model_simplifier(view_model_class):
    class ViewModelSimplifier(object):
        @staticmethod
        def serialize(obj):
            return obj.simplify()

        @classmethod
        def deserialize(cls, data_str):
            data = view_model_class.restore(data_str)
            return data

    return ViewModelSimplifier


class DateSimplifier(object):
    @staticmethod
    def serialize(data):
        return data.strftime('%Y-%m-%d')

    @classmethod
    def deserialize(cls, data_str):
        data = dt.datetime.strptime(data_str, '%Y-%m-%d').date()
        return data


class DateTimeSimplifier(object):
    @staticmethod
    def serialize(data):
        return data.strftime('%Y-%m-%dT%H:%M')

    @classmethod
    def deserialize(cls, data_str):
        try:
            data = dt.datetime.strptime(data_str, '%Y-%m-%dT%H:%M')
            return data
        except ValueError:
            data = dt.datetime.strptime(data_str, '%Y-%m-%dT%H:%M:%SZ')
            return data


class TimeSimplifier(object):
    @staticmethod
    def serialize(data):
        return data.strftime('%H:%M')

    @classmethod
    def deserialize(cls, data_str):
        try:
            data = dt.datetime.strptime(data_str, '%H:%M').time()
            return data
        except ValueError:
            data = dt.datetime.strptime(data_str, '%H:%M:%S').time()
            return data


class TimeStampSimplifier(object):
    DATE_FORMATS = ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f',
                    '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S.%fZ']

    @staticmethod
    def serialize(data):
        return data.timestamp()

    @classmethod
    def deserialize(cls, data_str):
        if isinstance(data_str, (int, float)):
            data = dt.datetime.fromtimestamp(data_str)
            return data
        if data_str.isalnum():
            data = dt.datetime.fromtimestamp(int(data_str))
            return data
        for format in cls.DATE_FORMATS:
            try:
                data = dt.datetime.strptime(data_str, format)
                return data
            except ValueError:
                pass
        raise ValueError
