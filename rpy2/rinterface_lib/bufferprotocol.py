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

    shape: typing.Tuple[int, ...]
    if dim_cdata == openrlib.rlib.R_NilValue:
        shape = (openrlib.rlib.Rf_length(cdata), )
    else:
        _ = []
        for i in range(rk):
            _.append(openrlib.INTEGER_ELT(dim_cdata, i))
        shape = tuple(_)
    return shape


def getstrides(cdata, shape: typing.Tuple[int, ...],
               itemsize: int) -> typing.Tuple[int, ...]:
    rk = len(shape)
    strides = [itemsize, ]
    for i in range(1, rk):
        strides.append(shape[i-1] * strides[i-1])
    return tuple(strides)


def getbuffer(cdata):
    raise NotImplementedError()
