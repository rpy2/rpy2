import typing
from rpy2.rinterface_lib import openrlib


def getrank(cdata) -> int:
    dim_cdata = openrlib.rlib.Rf_getAttrib(cdata,
                                           openrlib.rlib.R_DimSymbol)
    if dim_cdata == openrlib.rlib.R_NilValue:
        return 1
    else:
        return openrlib.rlib.Rf_length(dim_cdata)


def getshape(cdata, rk: typing.Optional[int] = None) -> typing.Tuple[int, ...]:
    if rk is None:
        rk = getrank(cdata)
    dim_cdata = openrlib.rlib.Rf_getAttrib(cdata,
                                           openrlib.rlib.R_DimSymbol)
    shape = [None, ] * rk
    if dim_cdata == openrlib.rlib.R_NilValue:
        shape[0] = openrlib.rlib.Rf_length(cdata)
    else:
        for i in range(rk):
            shape[i] = openrlib.INTEGER_ELT(dim_cdata, i)
    return tuple(shape)


def getstrides(cdata, shape: typing.Tuple[int, ...],
               itemsize: int) -> typing.Tuple[int, ...]:
    rk = len(shape)
    strides = [None, ] * rk
    strides[0] = itemsize
    for i in range(1, rk):
        strides[i] = shape[i-1] * strides[i-1]
    return tuple(strides)


def getbuffer(cdata):
    raise NotImplementedError()
