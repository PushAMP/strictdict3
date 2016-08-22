"""
Validators check objects on asignment and do coercion if needed
"""
import datetime as dt
import decimal


class ValidationError(Exception):

    def __init__(self, message, class_=None, path=None, value=None,
                 errors=None, *args, **kwargs):
        if errors is None:
            errors = []
        self.errors = errors
        self.path = path or []
        self.value = value
        self.class_ = class_
        self.message = message
        super(ValidationError, self).__init__(*args, **kwargs)

    def __str__(self):
        clsname = self.class_.__name__ if self.class_ else '<No class>'
        path_display = ".".join([str(clsname)] + list(reversed(self.path)))
        return "Failed to validate {0} as {1}: {2}".format(
            self.value, path_display, self.message)


def DummyValidator(data):
    "Passes through whatever comes to it"
    return data


def SimpleTypeValidator(_type, error_classes=[ValueError]):
    def validator(data):
        error_msg = "Failed to validate as %s" % _type
        try:
            return _type(data)
        except tuple(error_classes) as e:
            raise ValidationError("{0}: {1}".format(error_msg, e))
        except TypeError as e:
            raise ValidationError("{0}: {1}".format(error_msg, e))
    return validator


def StringValidator(data):
    if isinstance(data, str):
        return data
    raise ValidationError('Not a string')


def StringIntValidator(data):
    if isinstance(data, str):
        return data
    if isinstance(data, int):
        return str(data)
    raise ValidationError('Not a string')


def StringNumValidator(data):
    if isinstance(data, str):
        return data
    is_num = (isinstance(data, int) or isinstance(data, float))
    if is_num:
        return str(data)
    raise ValidationError('Not a string')


IntValidator = SimpleTypeValidator(int)


def DecimalValidator(data):
    if isinstance(data, float):
        data = str(data)
    return SimpleTypeValidator(
        decimal.Decimal, [decimal.InvalidOperation, ValueError])(data)


def CurrencyValidator(data):
    if not isinstance(data, str):
        raise ValidationError('Not a string')
    if len(data) != 3:
        raise ValidationError(
            'Currency can contain two letters only [%s]' % data)
    return str(data)


def DateTimeValidator(data):
    if isinstance(data, dt.datetime):
        return data
    if isinstance(data, str):
        try:
            return parse_datetime(data)
        except ValueError as e:
            raise ValidationError('Not a datetime [%s, %s]' % (data, e,))
    raise ValidationError('Not a datetime [%s]' % data)


def DateValidator(data):
    if isinstance(data, dt.datetime):
        return data.date()
    if isinstance(data, dt.date):
        return data
    if isinstance(data, str):
        try:
            return parse_date(data)
        except ValueError as e:
            raise ValidationError('Not a date [%s, %s]' % (data, e,))
    raise ValidationError('Not a date [%s]' % data)


def TimeValidator(data):
    if isinstance(data, dt.time):
        return data
    if isinstance(data, str):
        try:
            return parse_time(data)
        except ValueError as e:
            raise ValidationError('Not a time [%s, %s]' % (data, e,))
    raise ValidationError('Not a time [%s]' % data)


def TimeStampValidator(data):
    if isinstance(data, (int, float)):
        try:
            return dt.datetime.fromtimestamp(data)
        except (ValueError, TypeError) as exc:
            raise ValidationError('Not a timestamp [%s, %s]' % (data, exc,))
    elif isinstance(data, str):
        try:
            return dt.datetime.fromtimestamp(float(data))
        except (ValueError, TypeError) as exc:
            raise ValidationError('Not a timestamp [%s, %s]' % (data, exc,))
    elif isinstance(data, dt.datetime):
        return data
    raise ValidationError('Not a timestamp [%s]' % data)


def parse_datetime(s):
    parts = s.split('T')
    if len(parts) == 2:
        time_str = parts[1]
        if time_str[-1] == 'Z':
            time_str = time_str[:-1]
        return dt.datetime.combine(parse_date(parts[0]), parse_time(time_str))
    raise ValueError('Invalid datetime format')


def parse_date(s):
    parts = s.split('-')
    if len(parts) == 3:
        return dt.date(int(parts[0]), int(parts[1]), int(parts[2]))
    raise ValueError('Invalid date format')


def parse_time(s):
    parts = s.split(':')
    if len(parts) >= 2:
        s = 0
        mcs = 0
        if len(parts) == 3:
            mparts = parts[2].split('.')
            s = int(mparts[0])
            if len(mparts) > 1:
                mcs = int(mparts[1])
        return dt.time(int(parts[0]), int(parts[1]), s, mcs)
    raise ValueError('Invalid time format')
