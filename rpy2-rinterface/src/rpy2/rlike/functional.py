"""This module is deprecated."""

# TODO: delete after release 1.7.0 this is deprecated.
import warnings


def tapply(seq, tag, fun):
    """ Apply the function `fun` to the items in `seq`,
    grouped by the tags defined in `tag`.

    :param seq: sequence
    :param tag: any sequence of tags
    :param fun: function
    :rtype: list
    """
    warnings.warn(
        'tapply() is deprecated.',
        DeprecationWarning
    )

    if len(seq) != len(tag):
        raise ValueError("seq and tag should have the same length.")

    tag_grp = {}
    for i, t in enumerate(tag):
        try:
            tag_grp[t].append(i)
        except LookupError:
            tag_grp[t] = [i, ]

    res = [(tag, fun([seq[i] for i in ti])) for tag, ti in tag_grp.items()]
    return res


def listify(fun):
    """ Decorator to make a function apply
    to each item in a sequence, and return a list. """
    warnings.warn(
        'listify() is deprecated.',
        DeprecationWarning
    )

    def f(seq):
        res = [fun(x) for x in seq]
        return res
    return f


def iterify(fun):
    """ Decorator to make a function apply
    to each item in a sequence, and return an iterator. """
    warnings.warn(
        'iterify() is deprecated.',
        DeprecationWarning
    )

    def f(seq):
        for x in seq:
            yield fun(x)
    return f
