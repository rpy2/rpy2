"""
Utilities for manipulating or evaluating the R language.
"""

# TODO: uuid is used to create a temporary symbol. This is a ugly
#     hack to work around an issue with with calling R functions
#     (language objects seem to be evaluated when doing so from rpy2
#     but not when doing it from R).
import typing
import uuid
from rpy2.robjects import conversion
from rpy2.robjects.robject import RObject
import rpy2.rinterface as ri
_reval = ri.baseenv['eval']
_parse = ri.parse

try:
    _str2lang = ri.baseenv['str2lang']
except KeyError:
    _str2lang = ri.evalr('function(s) parse(text=s, keep.source=FALSE)[[1]]')


def eval(x: str, envir: typing.Optional[ri.SexpEnvironment] = None) -> ri.Sexp:
    """ Evaluate R code. If the input object is an R expression it
    evaluates it directly, if it is a string it parses it before
    evaluating it.

    By default the evaluation is performed in R's global environment
    but a specific environment can be specified.

    Args:
    - x (str): a string to be parsed and evaluated as R code
    - envir (rpy2.rinterface.SexpEnvironment): An optional R environment
    in which to evaluate the R code.
    Returns:
    The R objects resulting from the evaluation."""

    if envir is None:
        envir = ri.get_evaluation_context()
    if isinstance(x, str):
        p = _parse(x)
    else:
        p = x
    res = _reval(p, env=envir)
    res = conversion.rpy2py(res)
    return res


LangVector_VT = typing.TypeVar('LangVector_VT', bound='LangVector')


class LangVector(RObject, ri.LangSexpVector):
    """R language object.

    R language objects are unevaluated constructs using the R language.
    They can be found in the default values for named arguments, for example:
    ```r
    r_function(x, n = ncol(x))
    ```
    The default value for `n` is then the result of calling the R function
    `ncol()` on the object `x` passed at the first argument.
    """

    def __repr__(self):
        # TODO: hack to work around an issue with calling R functions
        #   with rpy2 (language objects seem to be evaluated). Without
        #   the issue, the representation should simply be
        #   ri.baseenv['deparse'](self)[0]
        tmp_r_var = str(uuid.uuid4())
        representation = None
        try:
            ri.globalenv[tmp_r_var] = self
            representation = ri.evalr('deparse(`{}`)'.format(tmp_r_var))[0]
        finally:
            del ri.globalenv[tmp_r_var]
        return 'Rlang( {} )'.format(representation)

    @classmethod
    def from_string(cls: typing.Type[LangVector_VT], s: str) -> LangVector_VT:
        """Create an R language object from a string.

        This creates an unevaluated R language object.

        Args:
            s: R source code in a string.

        Returns:
            An instance of the class the method is from (e.g., LangVector)
        """
        return cls(_str2lang(s))
