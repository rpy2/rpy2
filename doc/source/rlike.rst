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
:class:`ArgsDict` and :class:`TaggedList` are structures
with which containeed items/elements can be tagged.

The module can be imported as follows:

>>> import rpy2.rlike.container as rlc


.. index::
   single: ArgsDict

ArgsDict
--------

The :class:`ArgsDict` proposes an implementation of what is
sometimes referred to in Python as an ordered dictionnary, with a
particularity: a key ``None`` means that, although an item has a rank
and can be retrieved from that rank, it has no "name".

In the hope of simplifying its usage, the API for an ordered dictionnary
in :pep:`372` was implemented. An example of usage is:

>>> x = (('a', 123), ('b', 456), ('c', 789))
>>> nl = rlc.ArgsDict(x)


>>> nl['a']
123
>>> nl.index('a')
0

Not all elements have to be named, and specifying a key value equal
to `None` indicates a value for which no name is associated.


>>> nl[None] = 'no name'

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
>>> tl.settag(0, 'c')
>>> tl.tags()
('c', 'b', 'c')
>>> it = tl.iterontag('c')
>>> [x for x in it]
[1, 3]


The Python docstring for the class is:

.. autoclass:: rpy2.rlike.container.TaggedList
   :members: