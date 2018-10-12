"""NA (Non-Available) values in R."""

from . import _rinterface_capi as _rinterface
from . import embedded
from . import sexp


def singleton(cls, *args, **kwargs):
    instances = {}
    def _singleton():
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return _singleton


NA_Character = None
NA_Integer = None
NA_Logical = None
NA_Real = None
NA_Complex = None


@singleton
class NAINtegerType(int):

    def __init__(self, x):
        if not embedded.isready():
            raise RNotReadyError("The embedded R is not ready to use.")
        super().__init__(_rinterface.rlib.R_NaInt)

    def __repr__(self):
        return 'NA_integer_'

    def __bool__(self):
        raise ValueError('R value for missing integer value')


@singleton
class NACharacterType(sexp.CharSexp):

    def __init__(self, x):
        if not embedded.isready():
            raise RNotReadyError("The embedded R is not ready to use.")
        super().__init__(_rinterface.rlib.R_NaString)
    
    def __repr__(self):
        return 'NA_character_'

    def __bool__(self):
        raise ValueError('R value for missing character value')

        
@singleton
class NALogicalType(int):

    def __init__(self, x):
        if not embedded.isready():
            raise RNotReadyError("The embedded R is not ready to use.")
        super().__init__(_rinterface.rlib.R_NaInt)

    def __repr__(self) -> str:
        return 'NA'

    def __bool__(self) -> bool:
        raise ValueError('R value for missing boolean value')


@singleton
class NARealType(int):

    def __init__(self, x: float):
        if not embedded.isready():
            raise RNotReadyError("The embedded R is not ready to use.")
        super().__init__(_rinterface.rlib.R_NaReal)

    def __repr__(self) -> str:
        return 'NA_real_'

    def __bool__(self) -> bool:
        raise ValueError('R value for missing float value')



@singleton
class NAComplexType(complex):

    def __init__(self, x):
        if not embedded.isready():
            raise RNotReadyError("The embedded R is not ready to use.")
        na_complex = _rinterface.ffi.new('Rcomplex *',
                                         [NA_Real, NA_Real])
        super().__init__(NA_Real, NA_Real)

    def __repr__(self):
        return 'NA_complex_'

    def __bool__(self):
        raise ValueError('R value for missing complex value')
