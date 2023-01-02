"""Python Buffer Protocol for R arrays."""
import typing
from rpy2.rinterface_lib import openrlib


def getrank(cdata) -> int:
    """Get the rank (number of dimensions) of an R array.

    The R NULL will return a rank of 1.
    :param cdata: C data from cffi
    :return: The rank"""
    dim_cdata = openrlib.rlib.Rf_getAttrib(cdata,
                                           openrlib.rlib.R_DimSymbol)
    if dim_cdata == openrlib.rlib.R_NilValue:
        # TODO: Why isn't this 0?
        return 1
    else:
        return openrlib.rlib.Rf_length(dim_cdata)


def getshape(cdata, rk: typing.Optional[int] = None) -> typing.Tuple[int, ...]:
    """Get the shape (size for each dimension) of an R array.

    The rank of the array can optionally by passed. Note that is potentially
    an unsafe operation if the value for the rank in incorrect. It may
    result in a segfault.

    :param cdata: C data from cffi
    :return: A Tuple with the sizes. The length of the tuple is the rank.
    """
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
    """Get the strides (offsets in memory when walking along dimension)
    for an R array.

    The shape (see method `getshape`) and itemsize must be specified.
    Incorrect values are potentially unsage and result in a segfault.

    :param cdata: C data from cffi.
    :param shape: The shape of the array.
    :param itemsize: The size of (C sizeof) each item in the array.
    :return: A tuple with the strides. The length of the tuple is rank-1."""
    rk = len(shape)
    strides = [itemsize, ]
    for i in range(1, rk):
        strides.append(shape[i-1] * strides[i-1])
    return tuple(strides)


def getbuffer(cdata):
    raise NotImplementedError()
