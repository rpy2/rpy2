import inspect
import os
import re
import textwrap
import typing
from typing import Union
import warnings
from collections import OrderedDict
from rpy2.robjects.robject import RObjectMixin
import rpy2.rinterface as rinterface
from rpy2.robjects import help
from rpy2.robjects import conversion

from rpy2.robjects.packages_utils import (default_symbol_r2python,
                                          default_symbol_resolve,
                                          _map_symbols,
                                          _fix_map_symbols)


baseenv_ri = rinterface.baseenv

# Needed to avoid circular imports.
__formals = baseenv_ri.find('formals')
__args = baseenv_ri.find('args')
__is_null = baseenv_ri.find('is.null')


def _formals_fixed(func):
    tmp = __args(func)
    if __is_null(tmp)[0]:
        return rinterface.NULL
    else:
        return __formals(tmp)


# docstring_property and DocstringProperty
# from Bradley Froehle
# https://gist.github.com/bfroehle/4041015
def docstring_property(class_doc):
    def wrapper(fget):
        return DocstringProperty(class_doc, fget)
    return wrapper


class DocstringProperty(object):
    def __init__(self, class_doc, fget):
        self.fget = fget
        self.class_doc = class_doc

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self.class_doc
        else:
            return self.fget(obj)

    def __set__(self, obj, value):
        raise AttributeError("Cannot set the attribute")

    def __delete__(self, obj):
        raise AttributeError("Cannot delete the attribute")


def _repr_argval(obj):
    """ Helper functions to display an R object in the docstring.
    This a hack and will be hopefully replaced the extraction of
    information from the R help system."""
    try:
        size = len(obj)
        if size == 1:
            if obj[0].rid == rinterface.MissingArg.rid:
                # no default value
                s = None
            elif obj[0].rid == rinterface.NULL.rid:
                s = 'rinterface.NULL'
            else:
                s = str(obj[0][0])
        elif size > 1:
            s = '(%s, ...)' % str(obj[0][0])
        else:
            s = str(obj)
    except Exception:
        s = str(obj)
    return s


class Function(RObjectMixin, rinterface.SexpClosure):
    """ Python representation of an R function.
    """
    __local = baseenv_ri.find('local')
    __call = baseenv_ri.find('call')
    __assymbol = baseenv_ri.find('as.symbol')
    __newenv = baseenv_ri.find('new.env')

    _local_env = None

    def __init__(self, *args, **kwargs):
        super(Function, self).__init__(*args, **kwargs)
        self._local_env = self.__newenv(
            hash=rinterface.BoolSexpVector((True, ))
        )

    @docstring_property(__doc__)
    def __doc__(self) -> str:
        fm = _formals_fixed(self)
        doc = list(['Python representation of an R function.',
                    'R arguments:', ''])
        if fm is rinterface.NULL:
            doc.append('<No information available>')
        for key, val in zip(fm.do_slot('names'), fm):
            if key == '...':
                val = 'R ellipsis (any number of parameters)'
            doc.append('%s: %s' % (key, _repr_argval(val)))
        return os.linesep.join(doc)

    def __call__(self, *args, **kwargs):
        new_args = [conversion.py2rpy(a) for a in args]
        new_kwargs = {}
        for k, v in kwargs.items():
            # TODO: shouldn't this be handled by the conversion itself ?
            if isinstance(v, rinterface.Sexp):
                new_kwargs[k] = v
            else:
                new_kwargs[k] = conversion.py2rpy(v)
        res = super(Function, self).__call__(*new_args, **new_kwargs)
        res = conversion.rpy2py(res)
        return res

    def formals(self):
        """ Return the signature of the underlying R function
        (as the R function 'formals()' would).
        """
        res = _formals_fixed(self)
        res = conversion.rpy2py(res)
        return res

    def rcall(
            self,
            keyvals,
            environment: typing.Optional[rinterface.SexpEnvironment] = None
    ) -> rinterface.sexp.Sexp:
        """ Wrapper around the parent method
        rpy2.rinterface.SexpClosure.rcall(). """
        res = super(Function, self).rcall(keyvals, environment=environment)
        return res


class SignatureTranslatedFunction(Function):
    """ Python representation of an R function, where
    the names in named argument are translated to valid
    argument names in Python. """
    _prm_translate: Union[OrderedDict, dict] = {}

    def __init__(self, sexp: rinterface.SexpClosure,
                 init_prm_translate=None,
                 on_conflict='warn',
                 symbol_r2python=default_symbol_r2python,
                 symbol_resolve=default_symbol_resolve):
        super(SignatureTranslatedFunction, self).__init__(sexp)
        if init_prm_translate is None:
            self._prm_translate = OrderedDict()
        else:
            assert isinstance(init_prm_translate, dict)
            self._prm_translate = init_prm_translate

        formals = self.formals()
        if formals.__sexp__._cdata != rinterface.NULL.__sexp__._cdata:
            (symbol_mapping,
             conflicts,
             resolutions) = _map_symbols(
                 formals.names,
                 translation=self._prm_translate,
                 symbol_r2python=symbol_r2python,
                 symbol_resolve=symbol_resolve)

            msg_prefix = ('Conflict when converting R symbols'
                          ' in the function\'s signature:\n- ')
            exception = ValueError
            _fix_map_symbols(symbol_mapping,
                             conflicts,
                             on_conflict,
                             msg_prefix,
                             exception)
            symbol_mapping.update(resolutions)
            # TODO: Why was this done?
            # reserved_pynames = set(dir(self))

            self._prm_translate.update((k, v[0])
                                       for k, v in symbol_mapping.items())
        if hasattr(sexp, '__rname__'):
            # TODO: mypy does not use the line above and trips on
            # __rname__ being not always present.
            self.__rname__ = sexp.__rname__  # type: ignore

    def __call__(self, *args, **kwargs):
        prm_translate = self._prm_translate
        for k in tuple(kwargs.keys()):
            r_k = prm_translate.get(k, None)
            if r_k is not None:
                v = kwargs.pop(k)
                kwargs[r_k] = v
        return (super(SignatureTranslatedFunction, self)
                .__call__(*args, **kwargs))


pattern_link = re.compile(r'\\link\{(.+?)\}')
pattern_code = re.compile(r'\\code\{(.+?)\}')
pattern_samp = re.compile(r'\\samp\{(.+?)\}')


class DocumentedSTFunction(SignatureTranslatedFunction):

    def __init__(self, sexp: rinterface.SexpClosure,
                 init_prm_translate=None,
                 packagename: typing.Optional[str] = None):
        super(DocumentedSTFunction,
              self).__init__(sexp,
                             init_prm_translate=init_prm_translate)
        self.__rpackagename__ = packagename

    @docstring_property(__doc__)
    def __doc__(self):
        doc = ['Wrapper around an R function.',
               '',
               'The docstring below is built from the R documentation.',
               '']

        description = help.docstring(self.__rpackagename__,
                                     self.__rname__,
                                     sections=['\\description'])
        doc.append(description)

        fm = _formals_fixed(self)
        names = fm.do_slot('names')
        doc.append(self.__rname__+'(')
        for key, val in self._prm_translate.items():
            if key == '___':
                description = ('(was "..."). R ellipsis '
                               '(any number of parameters)')
            else:
                description = _repr_argval(fm[names.index(val)])
            if description is None:
                doc.append('    %s,' % key)
            else:
                doc.append('    %s = %s,' % (key, description))
        doc.extend((')', ''))
        package = help.Package(self.__rpackagename__)
        page = package.fetch(self.__rname__)
        doc.append('Args:')
        for item in page.arguments():
            description = ('%s  ' % os.linesep).join(item.value)
            doc.append(' '.join(('  ', item.name, ': ', description)))
            doc.append('')

        doc.append(
            help.docstring(self.__rpackagename__,
                           self.__rname__,
                           sections=['\\details'])
        )

        return os.linesep.join(doc)


# TODO: shouldn't this be in a more central place / or more general interest ?
_SCALAR_COMPAT_RTYPES = set(
    getattr(rinterface.RTYPES, name).value
    for name in ('STRSXP', 'INTSXP', 'REALSXP', 'LGLSXP', 'CPLXSXP')
)


def _map_default_value(value: rinterface.Sexp):
    """
    Map default in the R signature.

    Because of R's lazy evaluation some default might be unevaluated
    expressions.

    Args:
      value:
    """
    if value.__sexp__.typeof in _SCALAR_COMPAT_RTYPES:
        # TODO: The dynamic check of typeof (to ensure that that
        # the underlying R object is of a compatible type makes
        # mypy trip. There is no way to check type outside of runtime.
        # Code refactoring would be needed.
        if len(value) == 1:  # type: ignore
            res = value[0]  # type: ignore
        else:
            res = value
    else:
        res = value
    return res


def map_signature(
        r_func: SignatureTranslatedFunction,
        is_method: bool = False,
        map_default: typing.Optional[
            typing.Callable[[rinterface.Sexp], typing.Any]
        ] = _map_default_value
) -> typing.Tuple[inspect.Signature, typing.Optional[int]]:
    """
    Map the signature of an function to the signature of a Python function.

    While mapping the signature, it will report the eventual presence of
    an R ellipsis.

    Args:
        r_func (SignatureTranslatedFunction): an R function
        is_method (bool): Whether the function should be treated as a method
            (adds a `self` param to the signature if so).
        map_default (function): Function to map default values in the Python
            signature. No mapping to default values is done if None.
    Returns:
        A tuple (inspect.Signature, int or None).
    """
    params = []
    r_ellipsis = None
    if is_method:
        params.append(inspect.Parameter('self',
                                        inspect.Parameter.POSITIONAL_ONLY))
    r_params = r_func.formals()
    rev_prm_transl = {v: k for k, v in r_func._prm_translate.items()}
    if r_params.names is not rinterface.NULL:
        for i, (name, default_orig) in enumerate(
                zip(r_params.names, r_params)
        ):
            if default_orig == '...':
                r_ellipsis = i
                warnings.warn('The R ellispsis is not yet well supported.')
            transl_name = rev_prm_transl.get(name)
            default_orig = default_orig[0]
            if map_default and not rinterface.MissingArg.rsame(default_orig):
                default_mapped = map_default(default_orig)
            else:
                default_mapped = inspect.Parameter.empty
            prm = inspect.Parameter(
                transl_name if transl_name else name,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=default_mapped
            )
            params.append(prm)
    return (inspect.Signature(params), r_ellipsis)


def wrap_docstring_default(
        r_func: SignatureTranslatedFunction,
        is_method: bool,
        signature: inspect.Signature,
        r_ellipsis: typing.Optional[int], *,
        full_repr: bool = False
) -> str:
    """
    Create a docstring that for a wrapped function.

    Args:
        r_func (SignatureTranslatedFunction): an R function
        is_method (bool): Whether the function should be treated as a method
            (a `self` parameter is added to the signature if so).
        signature (inspect.Signature): A mapped signature for `r_func`
        r_ellipsis (bool): Index of the parameter containing the R ellipsis
            (`...`). None if the R ellipsis is not in the function signature.
        full_repr (bool): Whether to have the full body of the R function in
            the docstring dynamically generated.
    Returns:
        A string.
    """
    docstring = []

    docstring.append('This {} wraps the following R function.'
                     .format('method' if is_method else 'function'))

    if r_ellipsis:
        docstring.extend(
            ('',
             textwrap.dedent(
                 """The R ellipsis "..." present in the function's parameters
                 is mapped to a python iterable of (name, value) pairs (such as
                 it is returned by the `dict` method `items()` for example."""
             ),
             '')
        )
    if full_repr:
        docstring.append('\n{}'.format(r_func.r_repr()))
    else:
        r_repr = r_func.r_repr()
        i = r_repr.find('\n{')
        if i == -1:
            docstring.append('\n{}'.format(r_func.r_repr()))
        else:
            docstring.append('\n{}\n{{\n  ...\n}}'.format(r_repr[:i]))

    return '\n'.join(docstring)


def wrap_r_function(
        r_func: SignatureTranslatedFunction, name: str, *,
        is_method: bool = False, full_repr: bool = False,
        map_default: typing.Optional[
            typing.Callable[[rinterface.Sexp],
                            typing.Any]
            ] = _map_default_value,
        wrap_docstring: typing.Optional[
            typing.Callable[[SignatureTranslatedFunction,
                             bool,
                             inspect.Signature,
                             typing.Optional[int]],
                            str]
            ] = wrap_docstring_default
) -> typing.Callable:
    """
    Wrap an rpy2 function handle with a Python function of matching signature.

    Args:
        r_func (rpy2.robjects.functions.SignatureTranslatedFunction): The
        function to be wrapped.
        name (str): The name of the function.
        is_method (bool): Whether the function should be treated as a method
        (adds a `self` param to the signature if so).
        map_default (function): Function to map default values in the Python
        signature. No mapping to default values is done if None.
    Returns:
        A function wrapping an underlying R function.
    """
    name = name.replace('.', '_')

    signature, r_ellipsis = map_signature(r_func, is_method=is_method,
                                          map_default=map_default)

    if r_ellipsis:
        def wrapped_func(*args, **kwargs):
            new_args = (
                list((None, x) for x in rinterface.args[:r_ellipsis]) +
                list(args[r_ellipsis]) +
                list((None, x)
                     for x in args[min(r_ellipsis+1, len(args)-1):]) +
                list(kwargs.items()))
            value = r_func.rcall(new_args)
            return value
    else:
        def wrapped_func(*args, **kwargs):
            value = r_func(*args, **kwargs)
            return value

    if wrap_docstring:
        docstring = wrap_docstring(r_func, is_method, signature, r_ellipsis)
    else:
        docstring = 'This is a dynamically created wrapper for an R function.'

    wrapped_func.__name__ = name
    wrapped_func.__qualname__ = name
    # TODO: Open issue in mypy about __signature.
    # https://github.com/python/mypy/issues/5958
    # Ignore the type check for now.
    wrapped_func.__signature__ = signature  # type: ignore
    wrapped_func.__doc__ = docstring

    return wrapped_func
