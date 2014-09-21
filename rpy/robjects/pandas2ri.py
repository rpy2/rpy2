import rpy2.robjects as ro
import rpy2.robjects.conversion as conversion
import rpy2.rinterface as rinterface
from rpy2.rinterface import SexpVector, INTSXP

from pandas.core.frame import DataFrame as PandasDataFrame
from pandas.core.series import Series as PandasSeries
from pandas.core.index import Index as PandasIndex
from numpy import recarray

from collections import OrderedDict
from rpy2.robjects.vectors import DataFrame, Vector, ListVector, StrVector, IntVector, POSIXct

# pandas is requiring numpy. We add the numpy conversion will be
# activate in the function activate() below
import rpy2.robjects.numpy2ri as numpy2ri


ISOdatetime = rinterface.baseenv['ISOdatetime']

def pandas2ri(obj):
    if isinstance(obj, PandasDataFrame):
        od = OrderedDict()
        for name, values in obj.iteritems():
            if values.dtype.kind == 'O':
                od[name] = StrVector(values)
            else:
                od[name] = pandas2ri(values)
        return DataFrame(od)
    elif isinstance(obj, PandasIndex):
        if obj.dtype.kind == 'O':
            return StrVector(obj)
        else:
            # only other alternative to 'O' is integer, I think,
            # which goes straight to the numpy converter.
            return numpy2ri.numpy2ri(obj)        
    elif isinstance(obj, PandasSeries):
        if obj.dtype == '<M8[ns]':
            # time series
            d = [IntVector([x.year for x in obj]),
                 IntVector([x.month for x in obj]),
                 IntVector([x.day for x in obj]),
                 IntVector([x.hour for x in obj]),
                 IntVector([x.minute for x in obj]),
                 IntVector([x.second for x in obj])]
            res = ISOdatetime(*d)
            #FIXME: can the POSIXct be created from the POSIXct constructor ?
            # (is '<M8[ns]' mapping to Python datetime.datetime ?)
            res = POSIXct(res)
        else:
            # converted as a numpy array
            res = numpy2ri.numpy2ri(obj.values)
        # "index" is equivalent to "names" in R
        if obj.ndim == 1:
            res.do_slot_assign('names', ListVector({'x': pandas2ri(obj.index)}))
        else:
            res.do_slot_assign('dimnames', ListVector(pandas2ri(obj.index)))
        return res
    else:
        # pandas2ri should definitely not have to know which paths remain to be
        # converted by numpy2ri
        return numpy2ri.numpy2ri(obj)

def ri2pandas(o):
    # use the numpy converter first
    res = numpy2ri.ri2numpy(o)
    if isinstance(res, recarray):
        res = PandasDataFrame.from_records(res)

    return res

def activate():
    '''Set conversion paths back to pandas2ri versions

    This will straightforwardly override an existing numpy2ri.activate()
    '''
    conversion.py2ri = pandas2ri
    conversion.ri2ro = ri2pandas
    conversion.py2ro = numpy2ri.numpy2ro

def deactivate():
    '''Set conversion paths back to robjects defaults

    Note that this will also revert, e.g., numpy2ri.activate()
    '''
    conversion.py2ri = ro.default_py2ri
    conversion.ri2ro = ro.default_ri2ro
    conversion.py2ro = ro.default_py2ro
