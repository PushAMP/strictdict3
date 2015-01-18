# coding: utf-8
"""
Test behaviour of StrictDict mega-class
"""

import pytest

from strictdict import StrictDict
from strictdict import fields as f
from strictdict import ValidationError
from strictdict import api


class Leg(StrictDict):
    is_working = f.Bool()
    is_cool = f.Bool(required=False)
    number = f.Int()
    name = f.String()
    boot_size = f.Float(required=False)
    market_price = f.Decimal(required=False)
    boot_color = f.String(required=False)
    date = f.Date(required=False)


class Centipede(StrictDict):
    age = f.Int()
    legs = f.ViewModelField(class_=Leg, is_list=True)
    favorite_leg = f.ViewModelField(class_=Leg, required=False)


class Missing(object):
    pass


@pytest.fixture(scope='function')
def leg_data():
    return {
        'is_working': True,
        'is_cool': True,
        'number': 1,
        'name': "Martha",
        'boot_color': 'blue',
        'boot_size': 37.5,
        'market_price': '123.45',
    }


@pytest.fixture
def centipede():
    return Centipede(age=100, legs=[leg_data()] * 10, favorite_leg=leg_data())


@pytest.mark.parametrize(('key', 'value'), [
        # OK values
        (None, None),
        ('is_working', 1),
        ('is_working', False),
        ('is_cool', Missing()),
        ('number', 123),
        ('date', '2013-07-08'),
        ('number', '-11'),
        ('boot_color', None),  # OK because boot_color is not required
        ('name', u"Любимая нога дядюшки Лю"),
        ('boot_size', '42.0'),
        ('market_price', 123.45),  # floats ok
        ('market_price', 100500),
])
def test_create_ok(leg_data, key, value):
    if key:
        leg_data[key] = value
    if isinstance(value, Missing):
        del leg_data[key]
    try:
        Leg(**leg_data)
    except ValidationError as exc:
        pytest.fail("{key}={value} raised ValidationError: {exc}".format(
            key=key, value=value, exc=exc))


@pytest.mark.parametrize(('key', 'value'), [
        # Invalid values
        ('number', '123.1'),
        ('number', '-'),
        ('is_working', 'Kinda, yeah, like, whatever'),
        ('boot_size', 'abyr!'),
        ('market_price', 'Too expensive for your cheap ass'),
        # Missing values
        ('is_working', None),
        ('is_working', Missing()),
        ('name', None),
        ('name', Missing()),
        # Extra values
        ('abyr', 'valg'),
        ('glavryba', None)
])
def test_create_invalid(leg_data, key, value):
    if isinstance(value, Missing):
        del leg_data[key]
    else:
        leg_data[key] = value
    with pytest.raises(ValidationError):
        Leg(**leg_data)


@pytest.mark.parametrize(('desc', 'data'), [
    ("Pure dicts",
        {'legs': [leg_data()] * 10, 'favorite_leg': leg_data()}),
    ("Iterable: objects, non-iterable: dict",
     dict(legs=[Leg(**leg_data())] * 10, favorite_leg=leg_data())),
    ("Iterable: empty list, non-iterable: whatever",
        {'legs': [], 'favorite_leg': leg_data()}),
    ("Iterable: objects mixed with dicts, non-iterable: object",
        {'legs': [Leg(**leg_data())] * 5 + [leg_data()] * 3,
         'favorite_leg': Leg(**leg_data())})
])
def test_create_nested_dict(data, desc):
    try:
        Centipede(age=1, **data)
    except ValidationError as exc:
        pytest.fail("Failed in scenario %s: %s" % (desc, exc))


def test_invalid_nested_dict(leg_data):
    valid_leg = leg_data
    invalid_leg = leg_data.copy()
    invalid_leg['is_working'] = '568'

    # Invalid nested
    with pytest.raises(ValidationError):
        Centipede(**{'age': 1,
                   'legs': [valid_leg] * 10,
                   'favorite_leg': invalid_leg})

    # Invalid nested collection
    with pytest.raises(ValidationError):
        Centipede(**{'age': 1,
                   'legs': [valid_leg] * 10 + [invalid_leg],
                   'favorite_leg': valid_leg})

    # Missing required collection
    with pytest.raises(ValidationError):
        Centipede(**{'age': 1,
                    'favorite_leg': valid_leg})


def test_immutability(centipede):
    # Changing scalar attributes
    with pytest.raises(AttributeError):
        centipede.age = 2
    with pytest.raises(AttributeError):
        centipede.legs = []
    with pytest.raises(AttributeError):
        del centipede.age
    # Changing nested object
    with pytest.raises(AttributeError):
        centipede.favorite_leg.name = "Dummy leg"

    with pytest.raises(AttributeError):
        centipede.legs[0].is_working = False
    # Changing iterable length
    with pytest.raises(AttributeError):
        centipede.legs = centipede.legs[1:]

    with pytest.raises(AttributeError):
        centipede.legs.pop()


def test_empty(leg_data):
    class LotsOfEmpty(StrictDict):
        int_ = f.Int(required=False)
        bool_ = f.Bool(required=False)
        leg_ = f.ViewModelField(class_=Leg, required=False)
        strlist = f.String(is_list=True, required=False)

        def empty_checks(self):
            assert self.int_ is None
            assert self.bool_ is None
            assert self.leg_ is None
            assert self.strlist == tuple()

    nothing = LotsOfEmpty()
    nothing.empty_checks()
    # Serialization
    str_ = nothing.to_string()
    nothing_at_all = LotsOfEmpty.loads(str_)
    nothing_at_all.empty_checks()
    # Simplification
    dict_ = nothing.simplify()
    nothing_i_swear = LotsOfEmpty.restore(dict_)
    nothing_i_swear.empty_checks()


def test_to_string(centipede):
    str_ = centipede.to_string()
    restored = Centipede.loads(str_)

    assert centipede.age == restored.age
    assert centipede.legs[1].name == restored.legs[1].name
    assert centipede.favorite_leg.number == restored.favorite_leg.number


def test_dumps(centipede):
    str_ = Centipede.dumps([centipede, centipede])
    c1, c2 = Centipede.loads(str_)

    assert centipede.age == c1.age
    assert centipede.legs[1].name == c1.legs[1].name
    assert centipede.favorite_leg.number == c1.favorite_leg.number
    assert centipede.age == c2.age
    assert centipede.legs[1].name == c2.legs[1].name
    assert centipede.favorite_leg.number == c2.favorite_leg.number


def test_simplify_restore(centipede):
    d = centipede.simplify()
    restored = Centipede.restore(d)

    assert centipede.age == restored.age
    assert centipede.legs[1].name == restored.legs[1].name
    assert centipede.favorite_leg.number == restored.favorite_leg.number


def test_unknown_fields_ignore():
    class Class_v1(StrictDict):
        field1 = f.String(required=True)

    class Class_v2(StrictDict):
        field1 = f.String(required=True)
        field2 = f.String(required=True)

    c2 = Class_v2(field1='f1', field2='f2')
    c2_string = c2.to_string()

    c1 = Class_v1.loads(c2_string)
    c1_dict = dict(**c1)
    assert len(c1_dict) == 1


def test_iteration_for_partial_strict_dict():
    class Class_v1(StrictDict):
        field1 = f.String(required=True)

    class Class_v2(StrictDict):
        field1 = f.String(required=True)
        field2 = f.String(required=True)

    c1 = Class_v1(field1='f1')
    c1_string = c1.to_string()

    c2 = Class_v2.loads(c1_string)
    c2_dict = dict(**c2)
    assert len(c2_dict) == 1


def test_to_dict():
    class SampleInner(StrictDict):
        field1 = f.String(required=True)
        field2 = f.Decimal(required=True)

    class Sample(StrictDict):
        field3 = f.ViewModelField(SampleInner, required=True)
        field4 = f.Decimal(required=True, is_list=True)
        field5 = f.ViewModelField(SampleInner, required=True, is_list=True)

    si = SampleInner(field1='field1', field2=2)
    si2 = SampleInner(field1='field1_2', field2=22)
    s = Sample(field3=si, field4=[1, 2, 3, 4], field5=[si, si2])

    s_dict = s.to_dict()
    assert s_dict['field3']['field1'] == 'field1'
    assert s_dict['field3']['field2'] == 2
    assert s_dict['field4'] == tuple([1, 2, 3, 4])
    assert s_dict['field5'][0]['field1'] == 'field1'
    assert s_dict['field5'][1]['field1'] == 'field1_2'
    assert len(s_dict['field5']) == 2


def test_inheritance():
    class Class_v1(StrictDict):
        __ignored_fields__ = ['field3']
        field1 = f.String(required=True)
        field2 = f.String(required=True)

    class Class_v2(Class_v1):
        field1 = f.Int(required=True)
        field2 = f.String(required=True)
        field3 = f.String(required=True)

    with pytest.raises(ValidationError):
        Class_v2(field1='string1', field2='string2', field3='string3')

    assert 'field3' in Class_v2.__ignored_fields__
    resp = Class_v2(field1=1, field2='string2', field3='string3')
    assert resp
    assert 'field3' not in resp


def test_api():
    class Class_v1(StrictDict):
        field1 = api.ref(f.Int)

    class Class_v2(StrictDict):
        field1 = api.opt(f.Int)

    class Class_v3(StrictDict):
        field1 = api.slist(f.Int)

    class Class_v4(StrictDict):
        field1 = api.optlist(f.Int)

    class Class_v5(StrictDict):
        field1 = api.ref(Class_v1)

    v1 = Class_v1(field1=1)
    assert v1.field1 == 1

    v2 = Class_v2()
    assert v2.field1 is None

    v3 = Class_v3(field1=[1])
    assert isinstance(v3.field1, tuple)
    assert len(v3.field1) == 1
    assert v3.field1[0] == 1

    v4 = Class_v4()
    assert isinstance(v4.field1, tuple)
    assert len(v4.field1) == 0

    v5 = Class_v5(field1=Class_v1(field1=5))
    assert v5.field1.field1 == 5


def test_map_field():
    class Class_v1(StrictDict):
        field1 = api.ref(
            f.MapField,
            api.ref(f.String),
            api.slist(f.Int)
        )

    v1 = Class_v1(field1={'k1': [], 'k2': [1, 2, 3]})
    assert len(v1.field1) == 2
    assert len(v1.field1['k1']) == 0
    assert len(v1.field1['k2']) == 3
    assert v1.field1['k2'][0] == 1
    assert v1.field1['k2'][1] == 2
    assert v1.field1['k2'][2] == 3


def test_load_from_list():
    class Class_v1(StrictDict):
        field = f.Int()

    test_str = '[{"field": 1}, {"field": 2}]'
    res = Class_v1.loads(test_str)
    assert len(res) == 2
    assert res[0].field == 1
    assert res[1].field == 2


def tests_sets():
    class Collector(StrictDict):
        stuff = api.sset(f.String)

    c = Collector(stuff={'mac', 'iphone', 'ipad', 'ipod', 'mac'})
    assert isinstance(c.stuff, frozenset)
    dump = c.to_string()
    restore = Collector.loads(dump)
    assert isinstance(c.stuff, frozenset)
    dump = c.to_string(msg_pack=True)
    restore = Collector.loads(dump, msg_pack=True)
    assert isinstance(c.stuff, frozenset)


def tests_name_collision():
    ex = 'Nothing raised'
    try:
        class BadGuy(StrictDict):
            pop = f.String()
    except Exception as e:
        ex = e
    assert ex.__class__.__name__ == 'NameCollisionError'
