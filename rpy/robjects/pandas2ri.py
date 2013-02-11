import rpy2.robjects as ro
import rpy2.robjects.conversion as conversion
import rpy2.rinterface as rinterface
from rpy2.rinterface import SexpVector, INTSXP

import pandas.core.frame

from collections import OrderedDict
from rpy2.robjects.vectors import DataFrame, Vector, ListVector, StrVector

# pandas is requiring numpy. We add the numpy conversion as implicit
import rpy2.robjects.numpy2ri as numpy2ri
numpy2ri.activate()

original_conversion = conversion.py2ri

def pandas2ri(obj):
    if isinstance(obj, pandas.core.frame.DataFrame):
        od = OrderedDict()
        for name, values in obj.iteritems():
            if values.dtype.kind == 'O':
                od[name] = StrVector(values)
            else:
                od[name] = ro.conversion.py2ri(values)
        return DataFrame(od)
    else:
        return original_conversion(obj) 

def ri2pandas(o):
    if isinstance(o, DataFrame):
        #pass
        NotImplementedError("Conversion from rpy2 DataFrame to pandas' DataFrame")
    else:
        res = ro.default_ri2py(o)
    return res

def activate():
    conversion.py2ri = pandas2ri
    conversion.ri2py = ri2pandas 

