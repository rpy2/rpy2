""" Utility module with functions related to R packages
(having these in this utility module rather than in packages.py
prevents circular imports). """

from rpy2 import rinterface
from warnings import warn
from collections import defaultdict

_packages = rinterface.baseenv['.packages']
_libpaths = rinterface.baseenv['.libPaths']
_find_package = rinterface.baseenv['find.package']


def get_packagepath(package: str) -> str:
    """ return the path to an R package installed """
    res = _find_package(rinterface.StrSexpVector((package, )))
    return res[0]


# Functions to translate R symbols to Python symbols.
# The functions are in this module in order to facilitate
# their access from other modules (without circular dependencies).
# It is not necessarily the absolute best place to have the functions though.
def default_symbol_r2python(rname: str) -> str:
    """Replace each dot (.) with an underscore (_)."""
    return rname.replace('.', '_')


def default_symbol_resolve(symbol_mapping):
    """Resolve any conflict in a symbol mapping.

    The argument `symbol_mapping` maps candidate new symbol names
    (e.g., the names of Python attributes in the namespace returned by
    :func:`importr`)
    to a sequence of original symbol names (e.g., the names of objects in
    an R package). The purpose of this function is to resolved conflicts,
    that is situations where there is more than one original symbol name
    associated with a new symbol name.

    :param symbol_mapping: a :class:`dict` or dict-like object.
    :return: A 2-tuple with conflicts (a :class:`dict` mapping the new
    symbol to a sequence of symbols already matching) and resolutions (a
    :class:`dict` mapping new symbol).
    """
    # dict to store the Python symbol -> R symbols mapping causing problems.
    conflicts = dict()
    resolutions = dict()
    for py_symbol, r_symbols in symbol_mapping.items():
        n_r_symbols = len(r_symbols)
        if n_r_symbols == 1:
            continue
        elif n_r_symbols == 2:
            # more than one R symbol associated with this Python symbol
            try:
                idx = r_symbols.index(py_symbol)
                # there is an R symbol identical to the proposed Python symbol;
                # we keep that pair mapped, and change the Python symbol for
                # the other R symbol(s) according to PEP 0008
                for i, r_name in enumerate(r_symbols):
                    if i == idx:
                        resolutions[py_symbol] = [r_name, ]
                    else:
                        new_py_symbol = py_symbol + '_'
                        resolutions[new_py_symbol] = [r_name, ]
            except ValueError:
                # I am unsure about what to do at this point:
                # add it as a conflict
                conflicts[py_symbol] = r_symbols
        else:
            # no automatic resolution if more than 2
            conflicts[py_symbol] = r_symbols
    return conflicts, resolutions


def _map_symbols(rnames,
                 translation=dict(),
                 symbol_r2python=default_symbol_r2python,
                 symbol_resolve=default_symbol_resolve):
    """
    :param names: an iterable of rnames
    :param translation: a mapping for R name->python name
    :param symbol_r2python: a function to translate an R symbol into a
                            (presumably valid) Python symbol
    :param symbol_resolve: a function to check a prospective set of
                           translation and resolve conflicts if needed
    """
    symbol_mapping = defaultdict(list)
    for rname in rnames:
        if rname in translation:
            rpyname = translation[rname]
        else:
            rpyname = symbol_r2python(rname)
        symbol_mapping[rpyname].append(rname)
    conflicts, resolutions = symbol_resolve(symbol_mapping)

    return (symbol_mapping, conflicts, resolutions)


def _fix_map_symbols(symbol_mapping,
                     conflicts,
                     on_conflict,
                     msg_prefix,
                     exception):
    """
    :param symbol_mapping: as returned by `_map_symbols`
    :param conflicts: as returned by `_map_symbols`
    :param on_conflict: action to take if conflict
    :param msg_prefix: prefix for error message
    :param exception: exception to raise
    """
    if len(conflicts) > 0:
        msg = msg_prefix
        msg += '\n- '.join(('%s -> %s' %
                            (k, ', '.join(v))
                            for k, v in conflicts.items()))
        if on_conflict == 'fail':
            msg += ('\nTo turn this exception into a simple '
                    'warning use the parameter '
                    '`on_conflict="warn"`')
            raise exception(msg)
        elif on_conflict == 'warn':
            for k, v in conflicts.items():
                if k in v:
                    symbol_mapping[k] = [k, ]
                else:
                    del(symbol_mapping[k])
            warn(msg)
        else:
            raise ValueError('Invalid value for parameter "on_conflict"')
