import pytest
import sys
import textwrap
import rpy2.robjects as robjects
import rpy2.robjects.methods as methods
rinterface = robjects.rinterface


def test_set_accessors():
    robjects.r['setClass']("A", robjects.r('list(foo="numeric")'))
    robjects.r['setMethod']("length", signature="A",
                            definition = robjects.r("function(x) 123"))
    class A(methods.RS4):
        def __init__(self):
            obj = robjects.r['new']('A')
            super().__init__(obj)

    acs = (('length', None, True, None), )
    methods.set_accessors(A, "A", None, acs)
    a = A()
    assert a.length[0] == 123


def test_RS4Type_noaccessors():
    robjects.r['setClass']("Foo", robjects.r('list(foo="numeric")'))
    classdef = """
    from rpy2 import robjects
    from rpy2.robjects import methods
    class Foo(methods.RS4, metaclass=methods.RS4_Type):
        def __init__(self):
            obj = robjects.r['new']('Foo')
            super().__init__(obj)
    """
    code = compile(textwrap.dedent(classdef),
                   '<string>', 'exec')
    ns = dict()
    exec(code, ns)
    f = ns['Foo']()
    # TODO: test ?


def test_RS4_factory():
    rclassname = 'Foo'
    robjects.r['setClass'](rclassname, 
                           robjects.r('list(bar="numeric")'))
    obj = robjects.r['new'](rclassname)
    f_rs4i = methods.rs4instance_factory(obj)
    assert rclassname == type(f_rs4i).__name__


def test_RS4Type_accessors():
    robjects.r['setClass']("R_A", robjects.r('list(foo="numeric")'))
    robjects.r['setMethod']("length", signature="R_A",
                            definition = robjects.r("function(x) 123"))

    classdef = """
    from rpy2 import robjects
    from rpy2.robjects import methods
    class R_A(methods.RS4, metaclass=methods.RS4_Type):
        __accessors__ = (
            ('length', None,
             'get_length', False, 'get the length'),
            ('length', None,
             None, True, 'length'))
        def __init__(self):
            obj = robjects.r['new']('R_A')
            super().__init__(obj)            
    """
    code = compile(textwrap.dedent(classdef),
                   '<string>', 'exec')
    ns = dict()
    exec(code, ns)
    R_A = ns['R_A']
    class A(R_A):
        __rname__ = 'R_A'

    ra = R_A()
    assert ra.get_length()[0] == 123
    assert ra.length[0] == 123

    a = A()
    assert a.get_length()[0] == 123
    assert a.length[0] == 123


def test_getclassdef():
    robjects.r('library(stats4)')
    cr = methods.getclassdef('mle', packagename='stats4')
    assert not cr.virtual


def test_RS4Auto_Type():
    robjects.r('library(stats4)')
    class MLE(object,
              metaclass=robjects.methods.RS4Auto_Type):
        __rname__ = 'mle'
        __rpackagename__ = 'stats4'
    # TODO: test ?


def test_RS4Auto_Type_nopackname():
    robjects.r('library(stats4)')

    class MLE(object,
              metaclass=robjects.methods.RS4Auto_Type):
        __rname__ = 'mle'
    # TODO: test ?
