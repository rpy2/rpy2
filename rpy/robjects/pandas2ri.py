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

original_converter = None 

# pandas is requiring numpy. We add the numpy conversion will be
# activate in the function activate() below
import rpy2.robjects.numpy2ri as numpy2ri


ISOdatetime = rinterface.baseenv['ISOdatetime']

converter = conversion.make_converter()
py2ri, ri2ro, py2ro, ri2py = converter

@py2ri.register(PandasDataFrame)
def py2ri_pandasdataframe(obj):
    od = OrderedDict()
    for name, values in obj.iteritems():
        if values.dtype.kind == 'O':
            od[name] = StrVector(values)
        else:
            od[name] = conversion.py2ri(values)
    return DataFrame(od)


@py2ri.register(PandasIndex)
def py2ri_pandasindex(obj):
    if obj.dtype.kind == 'O':
        return StrVector(obj)
    else:
        # pandas2ri should definitely not have to know which paths remain to be
        # converted by numpy2ri
        # Answer: the thing is that pandas2ri builds on the conversion
        # rules defined by numpy2ri - deferring to numpy2ri is allowing
        # us to reuse that code.
        return numpy2ri.numpy2ri(obj)

@py2ri.register(PandasSeries)
def py2ri_pandasseries(obj):
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
        res.do_slot_assign('names', StrVector(tuple(str(x) for x in obj.index)))
    else:
        res.do_slot_assign('dimnames', SexpVector(conversion.py2ri(obj.index)))
    return res

@ri2py.register(SexpVector)
def ri2py_vector(obj):
    # use the numpy converter first
    res = numpy2ri.ri2py(obj)
    if isinstance(res, recarray):
        res = PandasDataFrame.from_records(res)
    return res

@ri2py.register(DataFrame)
def ri2py_dataframe(obj):
    # use the numpy converter
    recarray = numpy2ri.ri2py(obj)
    res = PandasDataFrame.from_records(recarray)
    return res

def activate():
    global original_converter
    # If module is already activated, there is nothing to do
    if original_converter is not None: 
        return

    original_converter = conversion.make_converter(template=conversion.converter)
    numpy2ri.activate()
    new_converter = conversion.make_converter(template=conversion.converter)
    numpy2ri.deactivate()

    for k,v in py2ri.registry.items():
        if k is object:
            continue
        new_converter.py2ri.register(k, v)

    for k,v in ri2ro.registry.items():
        if k is object:
            continue
        new_converter.ri2ro.register(k, v)
    
    for k,v in py2ro.registry.items():
        if k is object:
            continue
        new_converter.py2ro.register(k, v)

    for k,v in ri2py.registry.items():
        if k is object:
            continue
        new_converter.ri2py.register(k, v)

    conversion.converter = new_converter
    conversion.ri2ro, conversion.py2ri, conversion.py2ro, conversion.ri2py = new_converter

def deactivate():
    global original_converter

    # If module has never been activated or already deactivated,
    # there is nothing to do
    if original_converter is None:
        return

    conversion.converter = original_converter
    conversion.ri2ro, conversion.py2ri, conversion.py2ro, conversion.ri2py = original_converter

    original_converter = None

