import abc
import collections
import copy
import json
import msgpack

from ..validators import ValidationError
from ..fields import ViewModelField, Field

__ALL__ = ['StrictDict']


class StrictDictMeta(abc.ABCMeta):
    # ABCMeta is metaclass of collections.MutableMapping
    def __new__(meta, name, bases, dict_):
        fields = dict_.setdefault('__fields__', {})
        ignored_fields = set(dict_.setdefault('__ignored_fields__', []))
        for base_class in bases:
            if hasattr(base_class, '__fields__'):
                fields.update(base_class.__fields__)
            if hasattr(base_class, '__ignored_fields__'):
                ignored_fields.update(base_class.__ignored_fields__)

        for attrname, attr in list(dict_.items()):
            if isinstance(attr, Field):
                if any(hasattr(base, attrname) for base in bases):
                    raise NameCollisionError(attrname)
                fields[attrname] = dict_.pop(attrname)

        for ifield in ignored_fields:
            fields.pop(ifield, None)
        dict_['__ignored_fields__'] = ignored_fields
        dict_['__fields__'] = fields
        return super(StrictDictMeta, meta).__new__(meta, name, bases, dict_)


class _StrictDictInterface(collections.MutableMapping):
    def __repr__(self):
        return self.to_string()

    def __getitem__(self, key):
        try:
            return self._get_item(key)
        except AttributeError:
            raise KeyError('key "%s" does not exist' % key)

    def __contains__(self, key):
        if key not in self.__fields__:
            return False
        return key in self._storage or key in self._simplified

    def __setitem__(self, key, value):
        raise AttributeError("Object is immutable")

    def __delitem__(self, key):
        raise AttributeError("Object is immutable")

    def __delattr__(self, key):
        raise AttributeError("Object is immutable")

    def __getattr__(self, key):
        return self._get_item(key)

    def __setattr__(self, key, value):
        raise AttributeError("Object is immutable")

    def __len__(self):
        return len(self._keys())

    def __iter__(self):
        for key in self._keys():
            if key in self:
                yield key

    def __hash__(self):
        return hash(self.to_string(msg_pack=True))


class StrictDict(_StrictDictInterface, metaclass=StrictDictMeta):
    """
    Provides dict interface with validation and serialization/deserialization
    """
    __fields__ = {}
    __ignored_fields__ = ()
    is_ignore_unknown_fields = False

    def __init__(self, **kwargs):
        if self.is_ignore_unknown_fields:
            # Silently swallow all extra keys
            kwargs = {k: v for k, v in kwargs.items() if k in self.__fields__.keys()}

        # Underlying python dict
        self._direct_set('_storage', dict())
        # Simplified storage ready to be serialized
        self._direct_set('_simplified', dict())
        full_kwargs = kwargs
        kwargs = kwargs.copy()
        _errors = []
        for key, field in self.__fields__.items():
            value = kwargs.pop(key, None)
            value_is_empty = field.is_empty(value)
            if value_is_empty and field.required:
                exc = ValidationError('Required field {} is empty or missing!'.format(key), path=[],
                                      class_=self.__class__, value=full_kwargs)
                _errors.append({key: exc.message})
            elif value_is_empty:
                validated = field.empty_value()
            else:
                try:
                    validated = field.validate(value, key)
                except ValidationError as exc:
                    exc.class_ = self.__class__
                    if exc.errors:
                        value = exc.errors
                    else:
                        value = exc.message
                    _errors.append({key: value})

            if not _errors:
                self._storage[key] = validated
                if not value_is_empty:
                    self._simplified[key] = field.serialize(validated)

        if _errors:
            msg = 'ValidationError in fields: {}'.format(', '.join(self._format_error(_errors)))
            exc = ValidationError(msg, class_=self.__class__, path=[], value=full_kwargs, errors=_errors)
            raise exc

        extra_keys = set(kwargs.keys()) - set(self.__ignored_fields__)
        if extra_keys:
            raise ValidationError('No such fields: {}'.format(', '.join(str(x) for x in extra_keys)),
                                  class_=self.__class__)

    def _direct_set(self, key, value):
        object.__setattr__(self, key, value)

    def _format_error(self, errors, prefix=''):
        fields = []
        for error in errors:
            for key, value in error.items():
                if isinstance(value, list):
                    fields.extend(self._format_error(errors=value, prefix=key))
                else:
                    if prefix:
                        key = '{0}.{1}'.format(prefix, key)
                    fields.append(key)
        return fields

    def _keys(self):
        return self._simplified.keys()

    def _get_item(self, key):
        key = str(key)
        try:
            field = self.__fields__[key]
        except KeyError:
            raise AttributeError('No such field: "%s"' % key)

        if key in self._storage:
            # Value is ready
            return self._storage[key]
        if key in self._simplified:
            # Value is in simplified form
            val_simpl = self._simplified[key]
            value = field.deserialize(val_simpl)
            self._storage[key] = value
            return value
        self._storage[key] = value = field.empty_value()
        return value

    def simplify(self):
        return self._simplified

    def to_dict(self):
        """
        For backwards compatibility
        """
        plain_dict = dict()
        for k, v in self.items():
            if self.__fields__[k].is_list:
                if isinstance(self.__fields__[k], ViewModelField):
                    plain_dict[k] = tuple(vt.to_dict() for vt in v)
                    continue

                plain_dict[k] = tuple(copy.deepcopy(vt) for vt in v)
                continue

            if isinstance(self.__fields__[k], ViewModelField):
                plain_dict[k] = v.to_dict()
                continue

            plain_dict[k] = copy.deepcopy(v)

        return plain_dict

    @classmethod
    def restore(cls, data_dict):
        """
        Restore from previously simplified data. Data is supposed to be valid,
        no checks are performed!
        """
        obj = cls.__new__(cls)  # Avoid calling constructor
        object.__setattr__(obj, '_simplified', data_dict)
        object.__setattr__(obj, '_storage', dict())
        return obj

    def to_string(self, msg_pack=False):
        return self.dumps(self, msg_pack=msg_pack)

    @classmethod
    def dumps(cls, data, msg_pack=False):
        if isinstance(data, (list, tuple,)):
            data = [d.simplify() for d in data]
        else:
            data = data.simplify()

        if msg_pack:
            return msgpack.dumps(data)
        kw = {}
        return json.dumps(data, **kw)

    @classmethod
    def loads(cls, data_str, msg_pack=False):
        if msg_pack:
            if isinstance(data_str, bytes):
                data = msgpack.loads(data_str, encoding='utf-8')
            else:
                data = msgpack.loads(data_str)
        else:
            data = json.loads(data_str)

        if isinstance(data, (list, tuple,)):
            return [cls.restore(d) for d in data]
        return cls.restore(data)

    def clone(self):
        """
        Return a deep copy of self
        """
        return self.restore(self.simplify())


class NameCollisionError(Exception):
    pass
