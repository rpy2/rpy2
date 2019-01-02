import builtins
from . import openrlib


def getrank(cdata):
    dim_cdata = openrlib.rlib.Rf_getAttrib(cdata,
                                           openrlib.rlib.R_DimSymbol)
    if dim_cdata == openrlib.rlib.R_NilValue:
        return 1
    else:
        return openrlib.rlib.Rf_length(dim_cdata)


def getshape(cdata, rk=None):
    if rk is None:
        rk = getrank(cdata)
    dim_cdata = openrlib.rlib.Rf_getAttrib(cdata,
                                           openrlib.rlib.R_DimSymbol)
    shape = [None, ] * rk
    if dim_cdata == openrlib.rlib.R_NilValue:
        shape[0] = openrlib.rlib.Rf_length(cdata)
    else:
        for i in range(rk):
            shape[i] = openrlib.rlib.INTEGER_ELT(dim_cdata, i)
    return shape


def getstrides(cdata, shape, itemsize):
    rk = len(shape)
    strides = [None, ] * rk
    strides[0] = itemsize
    for i in range(1, rk):
        strides[i] = shape[i-1] * strides[i-1]
    return strides


def getbuffer(cdata):
    raise NotImplementedError()


def memoryview(obj: 'rpy2.rinterface.sexp.SexpVector',
               sizeof_str: str, cast_str: str) -> memoryview:
    """
    - sizeof_str: type in a string to use with ffi.sizeof()
        (for example "int")
    - cast_str: type in a string to use with memoryview.cast()
        (for example "i")
    """
    b = openrlib.ffi.buffer(
        obj._R_GET_PTR(obj.__sexp__._cdata),
        openrlib.ffi.sizeof(sizeof_str) * len(obj))
    shape = getshape(obj.__sexp__._cdata)
    # One could have expected to only need builtin Python
    # and do something like
    # ```
    # mv = memoryview(b).cast(cast_str, shape, order='F')
    # ```
    # but Python does not handle FORTRAN-ordered arrays without having
    # to write C extensions. We have to use numpy.
    # TODO: Having numpy a requirement just for this is a problem.
    import numpy
    a = numpy.frombuffer(b, dtype=cast_str).reshape(shape, order='F')
    mv = builtins.memoryview(a)
    return mv
