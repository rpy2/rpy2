import rpy2.robjects as ro
import rpy2.robjects.conversion as conversion
import rpy2.rinterface as rinterface
from rpy2.rinterface import SexpVector, INTSXP

from pandas.core.frame import DataFrame as PandasDataFrame
from pandas.core.series import Series as PandasSeries
from pandas.core.index import Index as PandasIndex

from collections import OrderedDict
from rpy2.robjects.vectors import DataFrame, Vector, ListVector, StrVector, IntVector, POSIXct

original_py2ri = None 
original_ri2ro = None 


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
        return original_py2ri(obj) 

def ri2pandas(o):
    if isinstance(o, DataFrame):
        # use the numpy converter
        recarray = numpy2ri.ri2numpy(o)
        res = PandasDataFrame.from_records(recarray)
    else:
        res = ro.default_ri2ro(o)
    return res

def activate():
    global original_py2ri, original_ri2ro

    # If module is already activated, there is nothing to do
    if original_py2ri: 
        return

    #FIXME: shouldn't the use of numpy conversion be made
    #       explicit in the pandas conversion ?
    #       (and this remove the need to activate it ?)
    numpy2ri.activate()
    original_py2ri = conversion.py2ri
    original_ri2ro = conversion.ri2ro
    conversion.py2ri = pandas2ri
    conversion.ri2ro = ri2pandas 

def deactivate():
    global original_py2ri, original_ri2ro

    # If module has never been activated or already deactivated,
    # there is nothing to do
    if not original_py2ri:
        return

    conversion.py2ri = original_py2ri
    conversion.ri2ro = original_ri2ro 
    original_py2ri = original_ri2ro = None
    numpy2ri.deactivate()
