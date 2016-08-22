import collections
from ..validators import *
from ..simplifiers import *


class Field(object):
    validator = None
    simplifier = None

    def __init__(self, required=True, is_list=False, is_set=False,
                 *args, **kwargs):
        self.required = required
        self.is_list = is_list
        self.is_set = is_set

    def _validate(self, data):
        return self.validator(data)

    def _validate_list(self, data):
        if not isinstance(data, collections.Iterable):
            raise ValidationError("Is not iterable!")
        return tuple(self._validate(x) for x in data)

    def _validate_set(self, data):
        if not isinstance(data, set) and not isinstance(data, frozenset):
            raise ValidationError("Is not set!")
        return frozenset(self._validate(x) for x in data)

    def validate(self, data, key=None):
        try:
            if self.is_list:
                return self._validate_list(data)
            if self.is_set:
                return self._validate_set(data)
            return self._validate(data)
        except ValidationError as exc:
            if not exc.value:
                exc.value = repr(data)
            exc.path.append(key)
            exc.class_ = self.__class__
            raise exc

    def serialize(self, data):
        if self.is_empty(data):
            return None
        if self.is_list or self.is_set:
            return tuple(self.simplifier.serialize(item) for item in data)
        return self.simplifier.serialize(data)

    def deserialize(self, serialized):
        if serialized is None:
            return self.empty_value()
        if self.is_list:
            return tuple(
                self.simplifier.deserialize(item) for item in serialized)
        if self.is_set:
            return frozenset(
                self.simplifier.deserialize(item) for item in serialized)
        return self.simplifier.deserialize(serialized)

    def is_empty(self, value):
        """
        Check value for being empty
        """
        if value is None:
            return True

    def empty_value(self):
        """
        What to return when value has not been set
        """
        if self.is_list:
            return tuple()
        if self.is_set:
            return frozenset()
        return None


class FieldAsIs(Field):
    simplifier = staticmethod(NullSimplifier)


class Bool(FieldAsIs):
    def _validate(self, data):
        if isinstance(data, (bool, int)):
            return bool(data)
        if isinstance(data, str):
            if data.lower() in ('false', '0'):
                return False
            if data.lower() in ('true', '1'):
                return True
        raise ValidationError(
            "Only ints, booleans and strings 'False'' and 'True' are accepted")


class Int(FieldAsIs):
    validator = staticmethod(IntValidator)

    def _validate(self, data):
        if isinstance(data, float):
            raise ValidationError("Floats not allowed")
        return self.validator(data)


class String(FieldAsIs):
    validator = staticmethod(StringValidator)


# as String, but allows int and long
# need it to workaround inconsitent data
class StringInt(FieldAsIs):
    validator = staticmethod(StringIntValidator)


# as String, but allows int, long and float
# need it to workaround inconsitent data
class StringNum(FieldAsIs):
    validator = staticmethod(StringNumValidator)


class Decimal(Field):
    validator = staticmethod(DecimalValidator)
    simplifier = staticmethod(DecimalSimplifier)


class Float(FieldAsIs):
    validator = staticmethod(SimpleTypeValidator(float))


class ViewModelField(Field):
    """
    Validator for a specific StrictDict subclass
    """

    def __init__(self, class_, *args, **kwargs):
        super(ViewModelField, self).__init__(*args, **kwargs)
        self.class_ = class_
        self.simplifier = view_model_simplifier(class_)

    def _validate(self, data):
        if isinstance(data, self.class_):
            return data
        if isinstance(data, collections.Mapping):
            return self.class_(**data)
        raise ValidationError("Not a valid {}!".format(self.class_))


class MapField(Field):
    """
    Validator for a specific StrictDict subclass
    """
    simplifier = staticmethod(NullSimplifier)

    def __init__(self, key_field, value_field, *args, **kwargs):
        super(MapField, self).__init__(*args, **kwargs)
        self.key_field = key_field
        self.value_field = value_field

    def _validate(self, data):
        if not isinstance(data, collections.Mapping):
            raise ValidationError("Not a valid {}!".format(self.class_))
        resp = dict()
        for k, v in data.items():
            key = self.key_field.validate(k)
            value = self.value_field.validate(v)
            resp[key] = value
        return resp


class Date(Field):
    validator = staticmethod(DateValidator)
    simplifier = staticmethod(DateSimplifier)


class DateTime(Field):
    validator = staticmethod(DateTimeValidator)
    simplifier = staticmethod(DateTimeSimplifier)


class Time(Field):
    validator = staticmethod(TimeValidator)
    simplifier = staticmethod(TimeSimplifier)


class TimeStamp(Field):
    validator = staticmethod(TimeStampValidator)
    simplifier = staticmethod(TimeStampSimplifier)
