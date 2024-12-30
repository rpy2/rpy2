import pytest
import rpy2.robjects as robjects
rinterface = robjects.rinterface


def test_init():
    fml = robjects.Formula('y ~ x')
    assert fml.rclass[0] == 'formula'


def test_getenvironment():
    fml = robjects.Formula('y ~ x')
    env = fml.getenvironment()
    assert env.rclass[0] == 'environment'


def test_setenvironment():
    fml = robjects.Formula('y ~ x')
    newenv = robjects.baseenv['new.env']()
    env = fml.getenvironment()
    assert not newenv.rsame(env)
    fml.setenvironment(newenv)
    env = fml.getenvironment()
    assert newenv.rsame(env)


def test_setenvironment_error():
    fml = robjects.Formula('y ~ x')
    with pytest.raises(TypeError):
        fml.setenvironment(rinterface.NA_Logical)
