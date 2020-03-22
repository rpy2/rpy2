"""NA (Non-Available) values in R."""
from rpy2.rinterface_lib import embedded
from rpy2.rinterface_lib import openrlib
from rpy2.rinterface_lib import sexp
from rpy2.rinterface_lib.sexp import Singleton
from rpy2.rinterface_lib.sexp import SingletonABC
import rpy2.rinterface_lib._rinterface_capi as _rinterface


NA_Character = None
NA_Integer = None
NA_Logical = None
NA_Real = None
NA_Complex = None


class NAIntegerType(int, metaclass=Singleton):

    def __new__(cls, *args, **kwargs):
        embedded.assert_isready()
        return super().__new__(cls, openrlib.rlib.R_NaInt)

    def __repr__(self) -> str:
        return 'NA_integer_'

    def __str__(self) -> str:
        return 'NA_integer_'

    def __bool__(self):
        raise ValueError('R value for missing integer value')


class NACharacterType(sexp.CharSexp, metaclass=SingletonABC):

    def __init__(self):
        embedded.assert_isready()
        super().__init__(
            sexp.CharSexp(
                _rinterface.SexpCapsule(openrlib.rlib.R_NaString)
            )
        )

    def __repr__(self) -> str:
        return 'NA_character_'

    def __str__(self) -> str:
        return 'NA_character_'

    def __bool__(self):
        raise ValueError('R value for missing character value')


class NALogicalType(int, metaclass=Singleton):

    def __new__(cls, *args, **kwargs):
        embedded.assert_isready()
        return super().__new__(cls, openrlib.rlib.R_NaInt)

    def __repr__(self) -> str:
        return 'NA'

    def __str__(self) -> str:
        return 'NA'

    def __bool__(self) -> bool:
        raise ValueError('R value for missing boolean value')


class NARealType(float, metaclass=Singleton):

    def __new__(cls, *args, **kwargs):
        embedded.assert_isready()
        return super().__new__(cls, openrlib.rlib.R_NaReal)

    def __repr__(self) -> str:
        return 'NA_real_'

    def __str__(self) -> str:
        return 'NA_real_'

    def __bool__(self) -> bool:
        raise ValueError('R value for missing float value')


class NAComplexType(complex, metaclass=Singleton):

    def __new__(cls, *args, **kwargs):
        embedded.assert_isready()
        return super().__new__(cls,
                               openrlib.rlib.R_NaReal,
                               openrlib.rlib.R_NaReal)

    def __repr__(self) -> str:
        return 'NA_complex_'

    def __str__(self) -> str:
        return 'NA_complex_'

    def __bool__(self):
        raise ValueError('R value for missing complex value')
