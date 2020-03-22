"""NA (Non-Available) values in R."""

import abc
from rpy2.rinterface_lib import embedded
from rpy2.rinterface_lib import openrlib
from rpy2.rinterface_lib import sexp
import rpy2.rinterface_lib._rinterface_capi as _rinterface


class Singleton(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        instances = cls._instances
        if cls not in instances:
            instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return instances[cls]


class SingletonABC(Singleton, abc.ABCMeta):
    pass


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


class NULLType(sexp.Sexp, metaclass=SingletonABC):
    """A singleton class for R's NULL."""

    def __init__(self):
        embedded.assert_isready()
        super().__init__(
            sexp.Sexp(
                _rinterface.UnmanagedSexpCapsule(
                    openrlib.rlib.R_NilValue
                )
            )
        )

    def __bool__(self) -> bool:
        """This is always False."""
        return False

    @property
    def __sexp__(self) -> _rinterface.SexpCapsule:
        return self._sexpobject

    @property
    def rid(self) -> int:
        return self._sexpobject.rid
