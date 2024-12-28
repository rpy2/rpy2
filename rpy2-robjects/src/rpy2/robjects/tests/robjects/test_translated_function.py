import pytest

import rpy2.rinterface as rinterface
import rpy2.robjects as robjects
import array

identical = rinterface.baseenv['identical']
Function = robjects.functions.Function
SignatureTranslatedFunction = robjects.functions.SignatureTranslatedFunction


def test_init_invalid():
    with pytest.raises(ValueError):
        SignatureTranslatedFunction('a')


def test_init():
    ri_f = rinterface.baseenv.find('rank')
    ro_f = SignatureTranslatedFunction(ri_f)        
    assert identical(ri_f, ro_f)[0] is True


def test_init_with_translation():
    ri_f = rinterface.baseenv.find('rank')
    ro_f = SignatureTranslatedFunction(
        ri_f,
        init_prm_translate = {'foo_bar': 'na.last'})
    assert identical(ri_f, ro_f)[0] is True


def test_call():
    ri_f = rinterface.baseenv.find('sum')
    ro_f = robjects.Function(ri_f)

    ro_v = robjects.IntVector(array.array('i', [1,2,3]))

    s = ro_f(ro_v)
    assert s[0] == 6
