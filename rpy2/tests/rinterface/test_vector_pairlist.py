import rpy2.rinterface as ri


ri.initr()


def test_init_from_r():
    pairlist = ri.baseenv.find('pairlist')
    pl = pairlist(a=ri.StrSexpVector(['1', ]),
                  b=ri.StrSexpVector(['3', ]))
    assert pl.typeof == ri.RTYPES.LISTSXP


def test_names():
    pairlist = ri.baseenv.find('pairlist')
    pl = pairlist(a=ri.StrSexpVector(['1', ]),
                  b=ri.StrSexpVector(['3', ]))
    assert tuple(pl.names) == ('a', 'b')


def test_getitem_pairlist():
    pairlist = ri.baseenv.find('pairlist')
    pl = pairlist(a=ri.StrSexpVector(['1', ]),
                  b=ri.StrSexpVector(['3', ]))
    # R's behaviour is that subsetting returns an R list
    y = pl[0]
    assert y.typeof == ri.RTYPES.VECSXP
    assert len(y) == 1
    assert y[0][0] == '1'
    assert y.names[0] == 'a'


def test_getslice_pairlist():
    pairlist = ri.baseenv.find('pairlist')
    vec = pairlist(a=ri.StrSexpVector(['1', ]),
                   b=ri.StrSexpVector(['3', ]),
                   c=ri.StrSexpVector(['6', ]))
    vec_slice = vec[0:2]
    assert vec_slice.typeof == ri.RTYPES.LISTSXP
    assert len(vec_slice) == 2
    assert tuple(vec_slice[0][0]) == ('1', )
    assert tuple(vec_slice[1][0]) == ('3', )
    assert tuple(vec_slice.names) == ('a', 'b')


def test_getslice_pairlist_issue380():
    # Checks that root of issue #380 is fixed
    vec = ri.baseenv['.Options']
    vec_slice = vec[0:2]
    assert len(vec_slice) == 2
    assert vec_slice.typeof == ri.RTYPES.LISTSXP
    assert vec.names[0] == vec_slice.names[0]
    assert vec.names[1] == vec_slice.names[1]
