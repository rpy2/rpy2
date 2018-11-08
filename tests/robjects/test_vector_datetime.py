import datetime
import pytest
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


def test_POSIXct_from_invalidpythontime():
    x = [time.struct_time(_dateval_tuple), 
         time.struct_time(_dateval_tuple)]
    x.append('foo')
    # string 'foo' does not have attribute 'tm_zone'  
    with pytest.raises(AttributeError):
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


