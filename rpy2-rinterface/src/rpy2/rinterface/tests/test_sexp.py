import copy
import gc
import pytest
import rpy2.rinterface as rinterface

rinterface.initr()


def test_invalid_init():
    with pytest.raises(ValueError):
        rinterface.Sexp('a')


def test_init_from_existing():
    sexp = rinterface.baseenv.find('letters')
    sexp_new = rinterface.Sexp(sexp)
    assert sexp_new._sexpobject is sexp._sexpobject


def test_typeof():
    assert isinstance(rinterface.baseenv.typeof, int)


def test_get():
    sexp = rinterface.baseenv.find('letters')
    assert sexp.typeof == rinterface.RTYPES.STRSXP

    sexp = rinterface.baseenv.find('pi')
    assert sexp.typeof == rinterface.RTYPES.REALSXP

    sexp = rinterface.baseenv.find('options')
    assert sexp.typeof == rinterface.RTYPES.CLOSXP


@pytest.mark.parametrize('cls',
                         (rinterface.IntSexpVector, rinterface.ListSexpVector))
def test_list_attrs(cls):
    x = cls((1, 2, 3))
    assert len(x.list_attrs()) == 0
    x.do_slot_assign('a', rinterface.IntSexpVector((33, )))
    assert len(x.list_attrs()) == 1
    assert 'a' in x.list_attrs()


def test_do_slot():
    sexp = rinterface.baseenv.find('.Platform')
    names = sexp.do_slot('names')
    assert len(names) > 1
    assert 'OS.type' in names


def test_names():
    sexp = rinterface.baseenv.find('.Platform')
    names = sexp.names
    assert len(names) > 1
    assert 'OS.type' in names


def test_names_set():
    sexp = rinterface.IntSexpVector([1, 2, 3])
    assert sexp.names.rid == rinterface.NULL.rid
    sexp.names = rinterface.StrSexpVector(['a', 'b', 'c'])
    assert len(sexp.names) > 1
    assert tuple(sexp.names) == ('a', 'b', 'c')


def test_names_set_invalid():
    sexp = rinterface.IntSexpVector([1, 2, 3])
    assert sexp.names.rid == rinterface.NULL.rid
    with pytest.raises(ValueError):
        sexp.names = ('a', 'b', 'c')


def test_do_slot_missing():
    sexp = rinterface.baseenv.find('pi')
    with pytest.raises(LookupError):
        sexp.do_slot('foo')


def test_do_slot_not_string():
    sexp = rinterface.baseenv.find('pi')
    with pytest.raises(ValueError):
        sexp.do_slot(None)


def test_do_slot_empty_string():
    sexp = rinterface.baseenv.find('pi')
    with pytest.raises(ValueError):
        sexp.do_slot('')


def test_do_slot_assign_create():
    sexp = rinterface.IntSexpVector([])
    slot_value = rinterface.IntSexpVector([3, ])
    sexp.do_slot_assign('foo', slot_value)
    slot_value_back = sexp.do_slot('foo')
    assert len(slot_value_back) == len(slot_value)
    assert all(x == y for x, y in zip(slot_value, slot_value_back))


def test_do_slot_reassign():
    sexp = rinterface.IntSexpVector([])
    slot_value_a = rinterface.IntSexpVector([3, ])
    sexp.do_slot_assign('foo', slot_value_a)
    slot_value_b = rinterface.IntSexpVector([5, 6])
    sexp.do_slot_assign('foo', slot_value_b)
    slot_value_back = sexp.do_slot('foo')
    assert len(slot_value_b) == len(slot_value_back)
    assert all(x == y for x, y in zip(slot_value_b, slot_value_back))


def test_do_slot_assign_empty_string():
    sexp = rinterface.IntSexpVector([])
    slot_value = rinterface.IntSexpVector([3, ])
    with pytest.raises(ValueError):
        sexp.do_slot_assign('', slot_value)


def test_sexp_rsame_true():
    sexp_a = rinterface.baseenv.find("letters")
    sexp_b = rinterface.baseenv.find("letters")
    assert sexp_a.rsame(sexp_b)


def test_sexp_rsame_false():
    sexp_a = rinterface.baseenv.find("letters")
    sexp_b = rinterface.baseenv.find("pi")
    assert not sexp_a.rsame(sexp_b)


def test_sexp_rsame_invalid():
    sexp_a = rinterface.baseenv.find("letters")
    with pytest.raises(ValueError):
        sexp_a.rsame('foo')


def test___sexp__():
    sexp = rinterface.IntSexpVector([1, 2, 3])
    sexp_count = sexp.__sexp_refcount__
    sexp_cobj = sexp.__sexp__
    d = dict(rinterface._rinterface.protected_rids())
    assert sexp_count == d[sexp.rid]
    assert sexp_count == sexp.__sexp_refcount__
    sexp2 = rinterface.IntSexpVector([4, 5, 6, 7])
    sexp2_rid = sexp2.rid
    sexp2.__sexp__ = sexp_cobj
    del(sexp)
    gc.collect()
    d = dict(rinterface._rinterface.protected_rids())
    assert d.get(sexp2_rid) is None


def test_rclass_get():
    sexp = rinterface.baseenv.find('character')(1)
    assert len(sexp.rclass) == 1
    assert sexp.rclass[0] == 'character'

    sexp = rinterface.baseenv.find('matrix')(0)
    if rinterface.evalr('R.version$major')[0] >= '4':
        assert tuple(sexp.rclass) == ('matrix', 'array')
    else:
        assert tuple(sexp.rclass) == ('matrix', )

    sexp = rinterface.baseenv.find('array')(0)
    assert len(sexp.rclass) == 1
    assert sexp.rclass[0] == 'array'

    sexp = rinterface.baseenv.find('new.env')()
    assert len(sexp.rclass) == 1
    assert sexp.rclass[0] == 'environment'


def test_rclass_get_sym():
    # issue #749
    fit = rinterface.evalr("""
    stats::lm(y ~ x, data=base::data.frame(y=1:10, x=2:11))
    """)
    assert tuple(fit[9].rclass) == ('call', )


def test_rclass_set():
    sexp = rinterface.IntSexpVector([1, 2, 3])
    sexp.rclass = rinterface.StrSexpVector(['foo'])
    assert len(sexp.rclass) == 1
    assert sexp.rclass[0] == 'foo'

    sexp.rclass = 'bar'
    assert len(sexp.rclass) == 1
    assert sexp.rclass[0] == 'bar'


def test_rclass_set_invalid():
    sexp = rinterface.IntSexpVector([1, 2, 3])
    with pytest.raises(TypeError):
        sexp.rclass = rinterface.StrSexpVector(123)


def test__sexp__wrongtypeof():
    sexp = rinterface.IntSexpVector([1, 2, 3])
    cobj = sexp.__sexp__
    sexp = rinterface.StrSexpVector(['a', 'b'])
    assert len(sexp) == 2
    with pytest.raises(ValueError):
        sexp.__sexp__ = cobj


def test__sexp__set():
    x = rinterface.IntSexpVector([1, 2, 3])
    x_s = x.__sexp__
    x_rid = x.rid
    # The Python reference count of the capsule is incremented,
    # not the rpy2 reference count
    assert x.__sexp_refcount__ == 1

    y = rinterface.IntSexpVector([4, 5, 6])
    y_count = y.__sexp_refcount__
    y_rid = y.rid
    assert y_count == 1

    assert x_rid in [elt[0] for elt in rinterface._rinterface.protected_rids()]
    x.__sexp__ = y.__sexp__
    # x_s is still holding a refcount to the capsule
    assert x_rid in [elt[0] for elt in rinterface._rinterface.protected_rids()]
    # when gone, the capsule will be collected and the id no longer preserved
    del(x_s)
    assert x_rid not in [elt[0] for elt in
                         rinterface._rinterface.protected_rids()]

    assert x.rid == y.rid
    assert y_rid == y.rid


@pytest.mark.xfail(reason='WIP')
def test_deepcopy():
    sexp = rinterface.IntSexpVector([1, 2, 3])
    assert sexp.named == 0
    rinterface.baseenv.find("identity")(sexp)
    assert sexp.named >= 2
    sexp2 = sexp.__deepcopy__()
    assert sexp.typeof == sexp2.typeof
    assert list(sexp) == list(sexp2)
    assert not sexp.rsame(sexp2)
    assert sexp2.named == 0
    # should be the same as above, but just in case:
    sexp3 = copy.deepcopy(sexp)
    assert sexp.typeof == sexp3.typeof
    assert list(sexp) == list(sexp3)
    assert not sexp.rsame(sexp3)
    assert sexp3.named == 0


def test_rid():
    globalenv_id = rinterface.baseenv.find('.GlobalEnv').rid
    assert globalenv_id == rinterface.globalenv.rid


def test_NULL_nonzero():
    assert not rinterface.NULL


def test_charsxp_encoding():
    encoding = rinterface.NA_Character.encoding
    assert encoding == rinterface.sexp.CETYPE.CE_NATIVE


def test_charsxp_nchar():
    v = rinterface.StrSexpVector(['abc', 'de', ''])
    cs = v.get_charsxp(0)
    assert cs.nchar() == 3
    cs = v.get_charsxp(1)
    assert cs.nchar() == 2
    cs = v.get_charsxp(2)
    assert cs.nchar() == 0


def test_missingtype():
    assert not rinterface.MissingArg
