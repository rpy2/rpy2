import datetime
try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo
import pytest

import time
from rpy2 import robjects
import rpy2.robjects.vectors

_dateval_tuple = (1984, 1, 6, 6, 22, 0, 1, 6, 0) 
_zones_str = (None, 'America/New_York', 'Australia/Sydney')


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


@pytest.fixture(scope='module', params=_zones_str)
def default_timezone_mocker(request):
    zone_str = request.param
    if zone_str:
        rpy2.robjects.vectors.default_timezone = zoneinfo.ZoneInfo(zone_str)
    yield zone_str
    rpy2.robjects.vectors.default_timezone = None


@pytest.mark.parametrize(
    'x',
    ([time.struct_time(_dateval_tuple), ] * 2,
     [datetime.datetime(*_dateval_tuple[:-2]), ] * 2)
)
def test_POSIXct_from_python_times(x, default_timezone_mocker):
    res = robjects.POSIXct(x)
    assert list(res.slots['class']) == ['POSIXct', 'POSIXt']
    assert len(res) == 2
    zone = default_timezone_mocker
    assert res.slots['tzone'][0] == (zone if zone else '')


@pytest.mark.parametrize('zone_str',
                         _zones_str[1:])
def test_POSIXct_from_python_timezone(zone_str):
    x = [
        datetime.datetime(*_dateval_tuple[:-2])
        .replace(tzinfo=zoneinfo.ZoneInfo(zone_str)),
    ] * 2
    res = robjects.POSIXct(x)
    assert list(res.slots['class']) == ['POSIXct', 'POSIXt']
    assert len(res) == 2
    assert res.slots['tzone'][0] == (zone_str if zone_str else '')


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


def test_POSIXct_datetime_from_timestamp(default_timezone_mocker):
    tzone = robjects.vectors.get_timezone()
    dt = [datetime.datetime(1900, 1, 1),
          datetime.datetime(1970, 1, 1),
          datetime.datetime(2000, 1, 1)]
    dt = [x.replace(tzinfo=tzone) for x in dt]
    ts = [x.timestamp() for x in dt]
    res = [robjects.POSIXct._datetime_from_timestamp(x, tzone) for x in ts]
    for expected, obtained in zip(dt, res):
        assert expected == obtained
