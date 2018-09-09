import pytest
import rpy2.rinterface as ri

ri.initr()


def test_init():
    rgetattr = ri.baseenv.get('::')
    formula = rgetattr('stats', 'formula')
    f = formula(ri.StrSexpVector(['y ~ x', ]))
    assert f.typeof == ri.RTYPES.LANGSXP


def test_init_invalid():
    seq = True
    with pytest.raises(ValueError):
        ri.LangSexpVector(seq)


def test_getitem():
    rgetattr = ri.baseenv.get('::')
    formula = rgetattr('stats', 'formula')
    f = formula(ri.StrSexpVector(['y ~ x', ]))
    y = f[0]
    assert y.typeof == ri.RTYPES.SYMSXP
    assert str(f[0]) == '~'
    assert str(f[1]) == 'y'
    assert str(f[2]) == 'x'
    
def test_setitem():
    rgetattr = ri.baseenv.get('::')
    formula = rgetattr('stats', 'formula')
    f = formula(ri.StrSexpVector(['y ~ x', ]))
    response = f[1]
    predictor = f[2]
    f[1] = predictor
    f[2] = response
    assert str(f[1]) == 'x'
    assert str(f[2]) == 'y'

