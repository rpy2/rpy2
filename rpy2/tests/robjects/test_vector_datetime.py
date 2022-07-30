import datetime
import pytest
import pytz
import time
from rpy2 import robjects

_dateval_tuple = (1984, 1, 6, 6, 22, 0, 1, 6, 0) 
_zones = (None, 'America/New_York', 'Australia/Sydney')


def test_POSIXlt_from_invalidpythontime():
    x = [time.struct_time(_dateval_tuple), 
         time.struct_time(_dateval_tuple)]
    x.append('foo')
    with pytest.raises(ValueError):
        robjects.POSIXlt(x)


def test_POSIXlt_from_pythontime():
    x = [time.struct_time(_dateval_tuple), 
         time.struct_time(_dateval_tuple)]
    res = robjects.POSIXlt(x)
    assert len(x) == 2


@pytest.mark.xfail(reason='wday mismatch between R and Python (issue #523)')
def test_POSIXlt_getitem():
    x = [time.struct_time(_dateval_tuple), 
         time.struct_time(_dateval_tuple)]
    res = robjects.POSIXlt(x)
    assert res[0] == x[0]


def testPOSIXlt_repr():
    x = [time.struct_time(_dateval_tuple), 
         time.struct_time(_dateval_tuple)]
    res = robjects.POSIXlt(x)
    s = repr(res)
    assert isinstance(s, str)


def test_POSIXct_from_invalidpythontime():
    x = [time.struct_time(_dateval_tuple), 
         time.struct_time(_dateval_tuple)]
    x.append('foo')
    # string 'foo' does not have attribute 'tm_zone'  
    with pytest.raises(AttributeError):
        robjects.POSIXct(x)


def test_POSIXct_from_invalidobject():
    x = ['abc', 3]
    with pytest.raises(TypeError):
        robjects.POSIXct(x)


def test_POSIXct_from_pythontime():
    x = [time.struct_time(_dateval_tuple),
         time.struct_time(_dateval_tuple)]

    try:
        for zone in _zones:
            robjects.vectors.default_timezone = pytz.timezone(zone) if zone else None
            res = robjects.POSIXct(x)
            assert list(res.slots['class']) == ['POSIXct', 'POSIXt']
            assert len(res) == 2
            assert res.slots['tzone'][0] == (zone if zone else '')
    finally:
        robjects.vectors.default_timezone = None


def testPOSIXct_fromPythonDatetime():
    x = [datetime.datetime(*_dateval_tuple[:-2]),
         datetime.datetime(*_dateval_tuple[:-2])]

    try:
        for zone in _zones:
            robjects.vectors.default_timezone = pytz.timezone(zone) if zone else None
            res = robjects.POSIXct(x)
            assert list(res.slots['class']) == ['POSIXct', 'POSIXt']
            assert len(res) == 2
            assert res.slots['tzone'][0] == (zone if zone else '')
    finally:
        robjects.vectors.default_timezone = None


def testPOSIXct_fromLocalizedPythonDatetime():
    for zone in _zones[1:]:
        dt = pytz.timezone(zone).localize(datetime.datetime(*_dateval_tuple[:-2]))
        x = [dt, dt]
        res = robjects.POSIXct(x)
        assert list(res.slots['class']) == ['POSIXct', 'POSIXt']
        assert len(res) == 2
        assert res.slots['tzone'][0] == (zone if zone else '')


def testPOSIXct_fromSexp():
    sexp = robjects.r('ISOdate(2013, 12, 11)')
    res = robjects.POSIXct(sexp)
    assert len(res) == 1


def testPOSIXct_repr():
    sexp = robjects.r('ISOdate(2013, 12, 11)')
    res = robjects.POSIXct(sexp)
    s = repr(res)
    assert s.endswith('[2013-12-1...]')


def testPOSIXct_getitem():
    dt = ((datetime.datetime(2014, 12, 11) - datetime.datetime(1970,1,1))
          .total_seconds())
    sexp = robjects.r('ISOdate(c(2013, 2014), 12, 11, hour = 0, tz = "UTC")')
    res = robjects.POSIXct(sexp)
    assert (res[1] - dt) == 0


def testPOSIXct_iter_localized_datetime():
    timestamp = 1234567890
    timezone = 'UTC'
    r_vec = robjects.r('as.POSIXct')(
        timestamp,
        origin='1960-01-01', tz=timezone)
    r_times = robjects.r('strftime')(r_vec,
                                     format="%H:%M:%S",
                                     tz=timezone)
    py_value = next(r_vec.iter_localized_datetime())
    assert r_times[0] == ':'.join(
        ('%i' % getattr(py_value, x) for x in ('hour', 'minute', 'second'))
    )


def test_POSIXct_datetime_from_timestamp():

    try:
        for zone in _zones:
            if not zone:
                continue
            robjects.vectors.default_timezone = pytz.timezone(zone)

            tzone = robjects.vectors.get_timezone()
            dt = [datetime.datetime(1900, 1, 1),
                  datetime.datetime(1970, 1, 1),
                  datetime.datetime(2000, 1, 1)]
            dt = [tzone.localize(x) for x in dt]
            ts = [x.timestamp() for x in dt]
            res = [robjects.POSIXct._datetime_from_timestamp(x, tzone) for x in ts]
            for expected, obtained in zip(dt, res):
                assert expected == obtained
    finally:
        robjects.vectors.default_timezone = None
