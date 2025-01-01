import pytest
import pickle
from io import BytesIO

import rpy2.rlike.container as rlc


class TestOrdDict(object):

    def test_new(self):
        with pytest.deprecated_call():
            nl = rlc.OrdDict()

        x = (('a', 123), ('b', 456), ('c', 789))
        with pytest.deprecated_call():
            nl = rlc.OrdDict(x)

    def test_new_invalid(self):
        with pytest.raises(TypeError):
            with pytest.deprecated_call():
                rlc.OrdDict({})

    def test_notimplemented_operators(self):
        with pytest.deprecated_call():
            nl = rlc.OrdDict()
            nl2 = rlc.OrdDict()
        assert nl == nl  # equivalent to `nl is nl`
        assert nl != nl2  # equivalent to `nl is not nl2`
        with pytest.raises(TypeError):
            nl > nl2
        with pytest.raises(NotImplementedError):
            reversed(nl)
        with pytest.raises(NotImplementedError):
            nl.sort()

    def test_repr(self):
        x = (('a', 123), ('b', 456), ('c', 789))
        with pytest.deprecated_call():
            nl = rlc.OrdDict(x)
        assert isinstance(repr(nl), str)

    def test_iter(self):
        x = (('a', 123), ('b', 456), ('c', 789))
        with pytest.deprecated_call():
            nl = rlc.OrdDict(x)
        for a, b in zip(nl, x):
            assert a == b[0]

    def test_len(self):
        with pytest.deprecated_call():
            x = rlc.OrdDict()
        assert len(x) == 0

        x['a'] = 2
        x['b'] = 1

        assert len(x) == 2

    def test_getsetitem(self):
        with pytest.deprecated_call():
            x = rlc.OrdDict()

        x['a'] = 1
        assert len(x) == 1
        assert x['a'] == 1
        assert x.index('a') == 0
        x['a'] = 2
        assert len(x) == 1
        assert x['a'] == 2
        assert x.index('a') == 0
        x['b'] = 1
        assert len(x) == 2
        assert x['b'] == 1
        assert x.index('b') == 1

    def test_get(self):
        with pytest.deprecated_call():
            x = rlc.OrdDict()
        x['a'] = 1
        assert x.get('a') == 1
        assert x.get('b') is None
        assert x.get('b', 2) == 2

    def test_keys(self):
        with pytest.deprecated_call():
            x = rlc.OrdDict()
        word = 'abcdef'
        for i,k in enumerate(word):
            x[k] = i
        for i,k in enumerate(x.keys()):
            assert word[i] == k

    def test_getsetitemwithnone(self):
        with pytest.deprecated_call():
            x = rlc.OrdDict()

        x['a'] = 1
        x[None] = 2
        assert len(x) == 2
        x['b'] = 5
        assert len(x) == 3
        assert x['a'] == 1
        assert x['b'] == 5
        assert x.index('a') == 0
        assert x.index('b') == 2

    def test_reverse(self):
        with pytest.deprecated_call():
            x = rlc.OrdDict()
        x['a'] = 3
        x['b'] = 2
        x['c'] = 1
        x.reverse()
        assert x['c'] == 1
        assert x.index('c') == 0
        assert x['b'] == 2
        assert x.index('b') == 1
        assert x['a'] == 3
        assert x.index('a') == 2

    def test_items(self):
        args = (('a', 5), ('b', 4), ('c', 3),
                ('d', 2), ('e', 1))
        with pytest.deprecated_call():
            x = rlc.OrdDict(args)
        it = x.items()
        for ki, ko in zip(args, it):
            assert ki[0] ==  ko[0]
            assert ki[1] == ko[1]

    def test_pickling(self):
        f = BytesIO()
        with pytest.deprecated_call():
            pickle.dump(rlc.OrdDict([('a', 1), ('b', 2)]), f)
        f.seek(0)
        with pytest.deprecated_call():
            od = pickle.load(f)
        assert od['a'] == 1
        assert od.index('a') == 0
        assert od['b'] == 2
        assert od.index('b') == 1


class TestNamedList(object):

    def test__add__(self):
        tl = rlc.NamedList((1,2,3), names=('a', 'b', 'c'))
        tl = tl + tl
        assert len(tl) == 6
        assert tuple(tl.names()) == ('a', 'b', 'c', 'a', 'b', 'c')
        assert tuple(tl) == (1,2,3,1,2,3)

    def test__delitem__(self):
        tl = rlc.NamedList((1,2,3), names=('a', 'b', 'c'))
        assert len(tl) == 3
        del tl[1]
        assert len(tl) == 2
        assert tuple(tl.names()) == ('a', 'c')
        assert tuple(tl) == (1, 3)

    def test__delslice__(self):
        tl = rlc.NamedList((1,2,3,4), names=('a', 'b', 'c', 'd'))
        del tl[1:3]
        assert len(tl) == 2
        assert tuple(tl.names()) == ('a', 'd')
        assert tuple(tl) == (1, 4)

    def test__iadd__(self):
        tl = rlc.NamedList((1,2,3), names=('a', 'b', 'c'))
        tl += tl
        assert len(tl) == 6
        assert tuple(tl.names()) == ('a', 'b', 'c', 'a', 'b', 'c')
        assert tuple(tl) == (1,2,3,1,2,3)

    def test__imul__(self):
        tl = rlc.NamedList((1,2), names=('a', 'b'))
        tl *= 3
        assert len(tl) == 6
        assert tuple(tl.names()) == ('a', 'b', 'a', 'b', 'a', 'b')
        assert tuple(tl) == (1,2,1,2,1,2)

    def test__init__(self):
        names = ('a', 'b', 'c')
        tl = rlc.NamedList((1,2,3), names=names)
        assert tuple(tl.names()) == names
        with pytest.raises(ValueError):
            rlc.NamedList((1,2,3), names = ('b', 'c'))

    def test__init__nonames(self):
        tl = rlc.NamedList((1,2,3))
        assert tuple(tl.names()) == (None, None, None)

    def test__setslice__(self):
        tl = rlc.NamedList((1,2,3,4), names=('a', 'b', 'c', 'd'))
        tl[1:3] = rlc.NamedList([5, 6])
        assert len(tl) == 4
        assert tuple(tl.names()) == ('a', None, None, 'd')
        assert tuple(tl) == (1, 5, 6, 4)

    def test_append_deprecated(self):
        tl = rlc.NamedList((1,2,3), names=('a', 'b', 'c'))
        assert len(tl) == 3
        with pytest.deprecated_call():
            tl.append(4, tag='a')
        assert len(tl) == 4
        assert tl[3] == 4
        assert tuple(tl.names()) == ('a', 'b', 'c', 'a')

    def test_append(self):
        tl = rlc.NamedList((1,2,3), names=('a', 'b', 'c'))
        assert len(tl) == 3
        tl.append(rlc.NamedItem('a', 4))
        assert len(tl) == 4
        assert tl[3] == 4
        assert tuple(tl.names()) == ('a', 'b', 'c', 'a')

    def test_extend(self):
        tl = rlc.NamedList((1,2,3), names=('a', 'b', 'c'))
        tl.extend(rlc.NamedList([4, 5]))
        assert tuple(tl.names()) == ('a', 'b', 'c', None, None)
        assert tuple(tl) == (1, 2, 3, 4, 5)

    def test_insert_deprecated(self):
        tl = rlc.NamedList((1,2,3), names=('a', 'b', 'c'))
        with pytest.deprecated_call():
            tl.insert(1, 4, tag = 'd')
        assert tuple(tl.names()) == ('a', 'd', 'b', 'c')
        assert tuple(tl) == (1, 4, 2, 3)

    def test_insert_deprecated(self):
        tl = rlc.NamedList((1,2,3), names=('a', 'b', 'c'))
        tl.insert(1, rlc.NamedItem('d', 4))
        assert tuple(tl.names()) == ('a', 'd', 'b', 'c')
        assert tuple(tl) == (1, 4, 2, 3)

    def test_items(self):
        tl = rlc.NamedList((1,2,3), names=('a', 'b', 'c'))
        assert tuple(tl.items()) == (rlc.NamedItem('a', 1),
                                     rlc.NamedItem('b', 2),
                                     rlc.NamedItem('c', 3))

    def test_iterontag(self):
        tl = rlc.NamedList((1,2,3), names=('a', 'b', 'a'))
        with pytest.deprecated_call():
            assert tuple(tl.iterontag('a')) == (1, 3)

    def test_names(self):
        tl = rlc.NamedList((1,2,3), names=('a', 'b', 'c'))
        assert tuple(tl.names()) == ('a', 'b', 'c')

    def test_pop(self):
        tl = rlc.NamedList((1,2,3), names=('a', 'b', 'c'))
        assert len(tl) == 3
        elt = tl.pop()
        assert elt == 3
        assert len(tl) == 2
        assert tuple(tl.names()) == ('a', 'b')
        assert tuple(tl) == (1, 2)

        elt = tl.pop(0)
        assert elt == 1
        assert len(tl) == 1
        assert tuple(tl.names()) == ('b', )

    def test_remove(self):
        tl = rlc.NamedList((1,2,3), names=('a', 'b', 'c'))
        assert len(tl) == 3
        tl.remove(2)
        assert len(tl) == 2
        assert tuple(tl.names()) == ('a', 'c')
        assert tuple(tl) == (1, 3)

    def test_reverse(self):
        tn = ['a', 'b', 'c']
        tv = [1,2,3]
        tl = rlc.NamedList(tv, names = tn)
        tl.reverse()
        assert len(tl) == 3
        assert tuple(tl.names()) == ('c', 'b', 'a')
        assert tuple(tl) == (3, 2, 1)

    def test_sort(self):
        tn = ['a', 'c', 'b']
        tv = [1,3,2]
        tl = rlc.NamedList(tv, names = tn)
        tl.sort()

        assert tuple(tl.names()) == ('a', 'b', 'c')
        assert tuple(tl) == (1, 2, 3)

    def test_setname(self):
        tn = ['a', 'b', 'c']
        tv = [1,2,3]
        tl = rlc.NamedList(tv, names = tn)
        tl.setname(1, 'z')
        assert tuple(tl.names()) == ('a', 'z', 'c')

    def test_from_items(self):
        tl = rlc.NamedList.from_items(
            (
                ('a', 1), ('b', 2), ('c', 3)
            )
        )
        assert tuple(tl.names()) == ('a', 'b', 'c')
        assert tuple(tl) == (1, 2, 3)

        tl = rlc.NamedList.from_items({'a':1, 'b':2, 'c':3})
        assert set(tl.names()) == set(('a', 'b', 'c'))
        assert set(tuple(tl)) == set((1, 2, 3))

    def test_pickle(self):
        tl = rlc.NamedList([1, 2, 3])
        tl_pickled = pickle.dumps(tl)
        tl_unpickled = pickle.loads(tl_pickled)
        assert tuple(tl) == tuple(tl_unpickled)
        assert tuple(tl.names()) == tuple(tl_unpickled.names())
