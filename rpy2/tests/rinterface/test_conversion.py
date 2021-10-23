import pytest
from rpy2.rinterface_lib import _rinterface_capi as _rinterface
import rpy2.rinterface_lib.conversion


def test__int_to_sexp():
    with pytest.raises(ValueError):
            rpy2.rinterface_lib.conversion._int_to_sexp(
                _rinterface._MAX_INT + 1
            )
