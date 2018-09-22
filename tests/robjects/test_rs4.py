import pytest
from rpy2 import robjects


@pytest.fixture(scope='module')
def set_class_A():
    robjects.r('setClass("A", representation(a="numeric", b="character"))')
    yield
    robjects.r('setClass("A")')

    
def test_slotnames():
    ainstance = robjects.r('new("A", a=1, b="c")')
    assert tuple(ainstance.slotnames()) == ('a', 'b')


def test_isclass(self):
    ainstance = robjects.r('new("A", a=1, b="c")')
    assert not ainstance.isclass("B")
    assert ainstance.isclass("A")


def test_validobject(self):
    ainstance = robjects.r('new("A", a=1, b="c")')
    assert ainstance.validobject()
    #FIXME: test invalid objects ?
