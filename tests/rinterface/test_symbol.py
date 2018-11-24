import pytest
import rpy2.rinterface as rinterface

rinterface.initr()


def test_new_invalid():
    x = 1
    with pytest.raises(TypeError):
        rinterface.SexpSymbol(x)


def test_new_missing():
    with pytest.raises(TypeError):
        rinterface.SexpSymbol()


def test_new_fromstring():
    symbol = rinterface.SexpSymbol('pi')
    evalsymbol = rinterface.baseenv['eval'](symbol)
    assert evalsymbol.rid == rinterface.baseenv['pi'].rid


def test_new_str():
    symbol = rinterface.SexpSymbol('pi')
    assert 'pi' == str(symbol)
