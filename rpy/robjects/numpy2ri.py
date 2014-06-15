import rpy2.robjects as ro
import rpy2.robjects.conversion as conversion
import rpy2.rinterface as rinterface
from rpy2.rinterface import SexpVector, ListSexpVector, \
    LGLSXP, INTSXP, REALSXP, CPLXSXP, STRSXP, VECSXP, NULL
import numpy

#from rpy2.robjects.vectors import DataFrame, Vector, ListVector

original_py2ri = None
original_ri2ro = None
original_py2ro = None 

# The possible kind codes are listed at
#   http://numpy.scipy.org/array_interface.shtml
_kinds = {
    # "t" -> not really supported by numpy
    "b": rinterface.LGLSXP,
    "i": rinterface.INTSXP,
    # "u" -> special-cased below
    "f": rinterface.REALSXP,
    "c": rinterface.CPLXSXP,
    # "O" -> special-cased below
    "S": rinterface.STRSXP,
    "U": rinterface.STRSXP,
    # "V" -> special-cased below
    #FIXME: datetime64 ?
    #"datetime64": 
    }

#FIXME: the following would need further thinking & testing on
#       32bits architectures 
_kinds['float64'] = rinterface.REALSXP

_vectortypes = (rinterface.LGLSXP,
                rinterface.INTSXP,
                rinterface.REALSXP,
                rinterface.CPLXSXP,
                rinterface.STRSXP)

def numpy2ri(o):
    """ Augmented conversion function, converting numpy arrays into
    rpy2.rinterface-level R structures. """
    # allow array-likes to also function with this module.
    if not isinstance(o, numpy.ndarray) and hasattr(o, '__array__'):
        o = o.__array__()
    if isinstance(o, numpy.ndarray):
        if not o.dtype.isnative:
            raise(ValueError("Cannot pass numpy arrays with non-native byte orders at the moment."))

        # Most types map onto R arrays:
        if o.dtype.kind in _kinds:
            # "F" means "use column-major order"
            vec = SexpVector(o.ravel("F"), _kinds[o.dtype.kind])
            dim = SexpVector(o.shape, INTSXP)
            #FIXME: no dimnames ?
            #FIXME: optimize what is below needed/possible ? (other ways to create R arrays ?)
            res = rinterface.baseenv['array'](vec, dim=dim)
        # R does not support unsigned types:
        elif o.dtype.kind == "u":
            raise(ValueError("Cannot convert numpy array of unsigned values -- R does not have unsigned integers."))
        # Array-of-PyObject is treated like a Python list:
        elif o.dtype.kind == "O":
            res = conversion.py2ri(list(o))
        # Record arrays map onto R data frames:
        elif o.dtype.kind == "V":
            if o.dtype.names is None:
                raise(ValueError("Nothing can be done for this numpy array type %s at the moment." % (o.dtype,)))
            df_args = []
            for field_name in o.dtype.names:
                df_args.append((field_name, 
                                conversion.py2ri(o[field_name])))
            res = ro.baseenv["data.frame"].rcall(tuple(df_args), ro.globalenv)
        # It should be impossible to get here:
        else:
            raise(ValueError("Unknown numpy array type."))
    else:
        res = ro.default_py2ri(o)
    return res

def numpy2ro(o):
    if isinstance(o, numpy.ndarray):
        res = numpy2ri(o)
        res = ro.vectors.rtypeof2rotype[res.typeof](res)
    else:
        res = ro.default_py2ro(o)
    return res
    
def ri2numpy(o):
    if isinstance(o, ListSexpVector):
        if 'data.frame' in o.rclass:
            # R "factor" vectors will not convert well by default
            # (will become integers), so we build a temporary list o2
            # with the factors as strings.
            o2 = list()
            # An added complication is that the conversion defined
            # in this module will make __getitem__ at the robjects
            # level return numpy arrays
            for column in rinterface.ListSexpVector(o):
                if 'factor' in column.rclass:
                    levels = tuple(column.do_slot("levels"))
                    column = tuple(levels[x-1] for x in column)
                o2.append(column)
            names = o.do_slot('names')
            if names is NULL:
                res = numpy.rec.fromarrays(o2)
            else:
                res = numpy.rec.fromarrays(o2, names=tuple(names))
        else:
            # not a data.frame, yet is it still possible to convert it
            res = ro.default_ri2ro(o)
    elif (o.typeof in _vectortypes) and (o.typeof != VECSXP):
        res = numpy.asarray(o)
    else:
        res = ro.default_ri2ro(o)
    return res


def activate():
    global original_py2ri, original_ri2ro, original_py2ro

    # If module is already activated, there is nothing to do
    if original_py2ri: 
        return

    original_py2ri = conversion.py2ri
    original_ri2ro = conversion.ri2ro
    original_py2ro = conversion.py2ro

    conversion.py2ri = numpy2ri
    conversion.ri2ro = ri2numpy 
    conversion.py2ro = numpy2ro

def deactivate():
    global original_py2ri, original_ri2ro, original_py2ro

    # If module has never been activated or already deactivated,
    # there is nothing to do
    if not original_py2ri:
        return

    conversion.py2ri = original_py2ri
    conversion.ri2ro = original_ri2ro
    conversion.py2ro = original_py2ro
    original_py2ri = original_ri2ro = original_py2ro = None
