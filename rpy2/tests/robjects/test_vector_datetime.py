import datetime
import pytest
import pytz
import time
from rpy2 import robjects

_dateval_tuple = (1984, 1, 6, 6, 22, 0, 1, 6, 0) 


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
    res = robjects.POSIXct(x)
    assert len(x) == 2


def testPOSIXct_fromPythonDatetime():
    x = [datetime.datetime(*_dateval_tuple[:-2]), 
         datetime.datetime(*_dateval_tuple[:-2])]
    res = robjects.POSIXct(x)
    assert len(x) == 2


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
