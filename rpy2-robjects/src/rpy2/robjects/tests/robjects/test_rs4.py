import pytest
from rpy2 import robjects


@pytest.fixture(scope='module')
def set_class_A():
    robjects.r('methods::setClass("A", representation(a="numeric", b="character"))')
    yield
    robjects.r('methods::removeClass("A")')

    
def test_slotnames(set_class_A):
    ainstance = robjects.r('new("A", a=1, b="c")')
    assert tuple(ainstance.slotnames()) == ('a', 'b')


def test_isclass(set_class_A):
    ainstance = robjects.r('new("A", a=1, b="c")')
    assert not ainstance.isclass("B")
    assert ainstance.isclass("A")


def test_validobject(set_class_A):
    ainstance = robjects.r('new("A", a=1, b="c")')
    assert ainstance.validobject()
    #FIXME: test invalid objects ?
