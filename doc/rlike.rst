*****
rlike
*****

.. module:: rpy2.rlike
   :platform: Unix, Windows
   :synopsis: Operate (a bit) like in R


Overview
========

The package proposes R features for a pure Python
context, that is without an embedded R running.



.. module:: rpy2.rlike.container

Containers
==========

The module contains data collection-type data structures. 
:class:`OrdDict` and :class:`TaggedList` are structures
with which contained items/elements can be tagged.

The module can be imported as follows:

>>> import rpy2.rlike.container as rlc


.. index::
   single: OrdDict

OrdDict
--------

The :class:`OrdDict` proposes an implementation of what is
sometimes referred to in Python as an ordered dictionnary, with a
particularity: a key ``None`` means that, although an item has a rank
and can be retrieved from that rank, it has no "name".

In the hope of simplifying its usage, the API for an ordered dictionnary
in :pep:`372` was implemented. An example of usage is:

>>> x = (('a', 123), ('b', 456), ('c', 789))
>>> nl = rlc.OrdDict(x)


>>> nl['a']
123
>>> nl.index('a')
0

Not all elements have to be named, and specifying a key value equal
to `None` indicates a value for which no name is associated.


>>> nl[None] = 'no name'

The Python docstring for the class is:

.. autoclass:: rpy2.rlike.container.OrdDict
   :members:



.. index::
   single: TaggedList

TaggedList
----------

A :class:`TaggedList` is a Python :class:`list` in which each item has
an associated `tag`.
This is similar to `named` vectors in R.

>>> tl = rlc.TaggedList([1,2,3])
>>> tl
[1, 2, 3]
>>> tl.tags()
(None, None, None)
>>> tl.settag(0, 'a')
>>> tl.tags()
('a', None, None)


>>> tl = rlc.TaggedList([1,2,3], tags=('a', 'b', 'c'))
>>> tl
[1, 2, 3]
>>> tl.tags()
('a', 'b', 'c')
>>> tl.settag(2, 'a')
>>> tl.tags()
('a', 'b', 'a')
>>> it = tl.iterontag('a')
>>> [x for x in it]
[1, 3]


>>> [(t, sum([i for i in tl.iterontag(t)])) for t in set(tl.itertags())]
[('a', 4), ('b', 2)]

The Python docstring for the class is:

.. autoclass:: rpy2.rlike.container.TaggedList
   :members:


.. module:: rpy2.rlike.functional

Tools for working with sequences
================================

Tools for working with objects implementing the
sequence protocol can be found here.


.. autofunction:: tapply

>>> import rpy2.rlike.functional as rlf
>>> rlf.tapply((1,2,3), ('a', 'b', 'a'), sum)
[('a', 4), ('b', 2)]

:class:`TaggedList` objects can be used with their tags
(although more flexibility can be achieved using their
method :meth:`iterontags`):

>>> import rpy2.rlike.container as rlc
>>> tl = rlc.TaggedList([1, 2, 3], tags = ('a', 'b', 'a'))
>>> rlf.tapply(tl, tl.tags(), sum)
[('a', 4), ('b', 2)]

.. module:: rpy2.rlike.indexing

Indexing
========

Much of the R-style indexing can be achieved with Python's list comprehension:

>>> l = ('a', 'b', 'c')
>>> l_i = (0, 2)
>>> [l[i] for i in l_i]
['a', 'c']

In `R`, negative indexes mean that values should be excluded. Again,
list comprehension can be used (although this is not the most efficient way):

>>> l = ('a', 'b', 'c') 
>>> l_i = (-1, -2)
>>> [x for i, x in enumerate(l) if -i not in l_i]
['a']

.. function:: order(seq, cmp = default_cmp, reverse = False)

   Give the order in which to take the items in the sequence `seq` and
   have them sorted.
   The optional function cmp should return +1, -1, or 0.

   :param seq: sequence
   :param cmp: function
   :param reverse: boolean
   :rtype: list of integers

>>> import rpy2.rlike.indexing as rli
>>> x = ('a', 'c', 'b')
>>> o = rli.order(x)
>>> o
[0, 2, 1]
>>> [x[i] for i in o]
['a', 'b', 'c']
