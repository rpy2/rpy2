"""NA (Non-Available) values in R."""
# TODO: Indicate the Python version(s) supported that require
# `import __future__ import annotations`.
from __future__ import annotations
import typing
if typing.TYPE_CHECKING:
    from rpy2.rinterface_lib import sexp

NA_Character: typing.Optional[sexp.NACharacterType] = None
NA_Integer: typing.Optional[sexp.NAIntegerType] = None
NA_Logical: typing.Optional[sexp.NALogicalType] = None
NA_Real: typing.Optional[sexp.NARealType] = None
NA_Complex: typing.Optional[sexp.NAComplexType] = None
