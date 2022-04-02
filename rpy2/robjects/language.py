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


def eval(
        x: typing.Union[str, ri.ExprSexpVector],
        envir: typing.Union[
            None,
            ri.SexpEnvironment, ri.NULLType,
            ri.ListSexpVector, ri.PairlistSexpVector, int,
            ri._MissingArgType] = None,
        enclos: typing.Union[
            None,
            ri.ListSexpVector, ri.PairlistSexpVector,
            ri.NULLType, ri._MissingArgType] = None
) -> RObject:
    """ Evaluate R code. If the input object is an R expression it
    evaluates it directly, if it is a string it parses it before
    evaluating it.

    By default the evaluation is performed in R's global environment
    but a specific environment can be specified.

    This function is a wrapper around rpy2.rinterface.evalr and
    rpy2.rinterface.evalr_expr.

    Args:
    - x (str or ExprSexpVector): a string to be parsed as R code and
    evaluated, or an R expression to be evaluated.
    - envir: An optional R environment where the R code will be
    evaluated.
    - enclos: An optional enclosure.
    Returns:
    The R objects resulting from the evaluation."""

    if envir is None:
        envir = ri.get_evaluation_context()
    if isinstance(x, str):
        res = ri.evalr(x, envir=envir, enclos=enclos)
    else:
        res = ri.evalr_expr(x, envir=envir, enclos=enclos)
    return conversion.rpy2py(res)


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
