import pytest
import rpy2.robjects as robjects
rinterface = robjects.rinterface
import rpy2.rlike.container as rlc

import array
import csv
import os
import tempfile


def test_init_from_taggedlist():
    letters = robjects.r.letters        
    numbers = robjects.r('1:26')
    df = robjects.DataFrame(rlc.TaggedList((letters, numbers),
                                           tags = ('letters', 'numbers')))

    assert df.rclass[0] == 'data.frame'


def test_init_from_RObject():
    numbers = robjects.r('1:5')
    dataf = robjects.DataFrame(numbers)
    assert len(dataf) == 5
    assert all(len(x) == 1 for x in dataf)

    rfunc = robjects.r('sum')
    with pytest.raises(ValueError):
        robjects.DataFrame(rfunc)

    rdataf = robjects.r('data.frame(a=1:2, b=c("a", "b"))')
    dataf = robjects.DataFrame(rdataf)
    # TODO: test ?


def test_init_from_OrdDict():
    od = rlc.OrdDict(c=(('a', robjects.IntVector((1,2))),
                        ('b', robjects.StrVector(('c', 'd')))
                        ))
    dataf = robjects.DataFrame(od)
    assert dataf.rx2('a')[0] == 1


def test_init_from_dict():
    od = {'a': robjects.IntVector((1,2)),
          'b': robjects.StrVector(('c', 'd'))}
    dataf = robjects.DataFrame(od)
    assert dataf.rx2('a')[0] == 1


def test_init_stringsasfactors():
    od = {'a': robjects.IntVector((1,2)),
          'b': robjects.StrVector(('c', 'd'))}
    dataf = robjects.DataFrame(od, stringsasfactor=True)
    assert isinstance(dataf.rx2('b'), robjects.FactorVector)
    dataf = robjects.DataFrame(od, stringsasfactor=False)
    assert isinstance(dataf.rx2('b'), robjects.StrVector)


def test_dim():
    letters = robjects.r.letters        
    numbers = robjects.r('1:26')
    df = robjects.DataFrame(rlc.TaggedList((letters, numbers),
                                           tags = ('letters', 'numbers')))
    assert df.nrow == 26
    assert df.ncol == 2


def test_from_csvfile():
    column_names = ('letter', 'value')
    data = (column_names,
            ('a', 1),
            ('b', 2),
            ('c', 3))
    fh = tempfile.NamedTemporaryFile(mode = "w", delete = False)
    csv_w = csv.writer(fh)
    csv_w.writerows(data)
    fh.close()
    dataf = robjects.DataFrame.from_csvfile(fh.name)
    assert isinstance(dataf, robjects.DataFrame)
    assert column_names == tuple(dataf.names)
    assert dataf.nrow == 3
    assert dataf.ncol == 2


def test_to_csvfile():
    fh = tempfile.NamedTemporaryFile(mode = "w", delete = False)
    fh.close()
    d = {'letter': robjects.StrVector('abc'),
         'value' : robjects.IntVector((1, 2, 3))}
    dataf = robjects.DataFrame(d)
    dataf.to_csvfile(fh.name)
    dataf = robjects.DataFrame.from_csvfile(fh.name)
    assert dataf.nrow == 3
    assert dataf.ncol == 2


def test_iter_col():
    dataf = robjects.r('data.frame(a=1:2, b=I(c("a", "b")))')
    col_types = [x.typeof for x in dataf.iter_column()]
    assert rinterface.RTYPES.INTSXP == col_types[0]
    assert rinterface.RTYPES.STRSXP == col_types[1]


def test_iter_row():
    dataf = robjects.r('data.frame(a=1:2, b=I(c("a", "b")))')
    rows = [x for x in dataf.iter_row()]
    assert rows[0][0][0] == 1
    assert rows[1][1][0] == 'b'


def test_colnames():
    dataf = robjects.r('data.frame(a=1:2, b=I(c("a", "b")))')
    assert dataf.rownames[0] == '1'
    assert dataf.rownames[1] == '2'


def test_colnames_set():
    dataf = robjects.r('data.frame(a=1:2, b=I(c("a", "b")))')
    dataf.colnames = robjects.StrVector('de')
    assert tuple(dataf.colnames) == ('d', 'e')


def test_rownames():
    dataf = robjects.r('data.frame(a=1:2, b=I(c("a", "b")))')
    assert tuple(dataf.colnames) == ('a', 'b')


def test_rownames_set():
    dataf = robjects.r('data.frame(a=1:2, b=I(c("a", "b")))')
    dataf.rownames = robjects.StrVector('de')
    assert tuple(dataf.rownames) == ('d', 'e')


def test_cbind():
    dataf = robjects.r('data.frame(a=1:2, b=I(c("a", "b")))')
    dataf = dataf.cbind(robjects.r('data.frame(a=1:2, b=I(c("a", "b")))'))
    assert dataf.ncol == 4
    assert len([x for x in dataf.colnames if x == 'a']) == 2

    dataf = robjects.r('data.frame(a=1:2, b=I(c("a", "b")))')
    dataf = dataf.cbind(a = robjects.StrVector(("c", "d")))
    assert dataf.ncol == 3
    assert len([x for x in dataf.colnames if x == 'a']) == 2


def test_rbind():
    dataf = robjects.r('data.frame(a=1:2, b=I(c("a", "b")))')
    dataf = dataf.rbind(dataf)
    assert dataf.ncol == 2
    assert dataf.nrow == 4


def test_head():
    dataf = robjects.r('data.frame(a=1:26, b=I(letters))')
    assert dataf.head(5).nrow == 5
    assert dataf.head(5).ncol == 2


def test_repr():
    dataf = robjects.r('data.frame(a=1:2, b=I(c("a", "b")))')
    s = repr(dataf)
    assert 'data.frame' in s.split(os.linesep)[1]


