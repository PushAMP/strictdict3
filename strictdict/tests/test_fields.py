# coding: utf-8

import pytest
from ..validators import ValidationError
from decimal import Decimal
import datetime as dt
from strictdict import fields as f


def test_string():
    ff = f.String()
    with pytest.raises(ValidationError):
        ff._validate(123)
    result = ff._validate('text')
    assert result == 'text'


def test_decimal():
    ff = f.Decimal()
    result = ff._validate(1870.20)
    assert result == Decimal('1870.2')


def test_time():
    ff = f.Time()
    result = ff._validate('10:11:12')
    assert result == dt.time(10, 11, 12)


def test_bool():
    ff = f.Bool()
    result = ff._validate('false')
    assert result is False
    result = ff._validate('true')
    assert result is True


def test_date():
    ff = f.DateTime()
    result = ff._validate('2013-11-18T00:00:00')
    assert result == dt.datetime(2013, 11, 18)


def test_date_with_z():
    ff = f.DateTime()
    result = ff._validate('2013-11-18T00:00:00Z')
    assert result == dt.datetime(2013, 11, 18)

    result = ff.deserialize("2013-11-18T00:00:00Z")
    assert result == dt.datetime(2013, 11, 18)


def test_timestamp():
    ff = f.TimeStamp()
    now = dt.datetime.now()
    result = ff._validate(now.timestamp())
    assert result == now
    result = ff._validate(int(now.timestamp()))
    assert result == now.replace(microsecond=0)
    now_str = now.strftime('%Y-%m-%dT%H:%M:%S.%f')
    result = ff.deserialize(now_str)
    assert result == now
    now_str = now.strftime('%Y-%m-%dT%H:%M:%S')
    result = ff.deserialize(now_str)
    assert result == now.replace(microsecond=0)
    result = ff.deserialize(now.timestamp())
    assert result == now
