from .. import fields as f
from ..strictbase import StrictDict


def strict_field_helper(f_class, *args, **kwargs):
    if issubclass(f_class, StrictDict):
        return f.ViewModelField(f_class, *args, **kwargs)

    return f_class(*args, **kwargs)


def opt(f_class, *args, **kwargs):
    kwargs['required'] = False
    kwargs['is_list'] = False
    kwargs['is_set'] = False
    return strict_field_helper(f_class, *args, **kwargs)


def ref(f_class, *args, **kwargs):
    kwargs['required'] = True
    kwargs['is_list'] = False
    kwargs['is_set'] = False
    return strict_field_helper(f_class, *args, **kwargs)


def optlist(f_class, *args, **kwargs):
    kwargs['required'] = False
    kwargs['is_list'] = True
    kwargs['is_set'] = False
    return strict_field_helper(f_class, *args, **kwargs)


def slist(f_class, *args, **kwargs):
    kwargs['required'] = True
    kwargs['is_list'] = True
    kwargs['is_set'] = False
    return strict_field_helper(f_class, *args, **kwargs)


def sset(f_class, *args, **kwargs):
    kwargs['required'] = True
    kwargs['is_list'] = False
    kwargs['is_set'] = True
    return strict_field_helper(f_class, *args, **kwargs)


def optset(f_class, *args, **kwargs):
    kwargs['required'] = False
    kwargs['is_list'] = False
    kwargs['is_set'] = True
    return strict_field_helper(f_class, *args, **kwargs)
