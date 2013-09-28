import os
from collections import OrderedDict
from rpy2.robjects.robject import RObjectMixin, RObject
import rpy2.rinterface as rinterface
#import rpy2.robjects.conversion as conversion
from . import conversion

baseenv_ri = rinterface.baseenv

#needed to avoid circular imports
_reval = rinterface.baseenv['eval']

__formals = baseenv_ri.get('formals')
__args = baseenv_ri.get('args')
#_genericsargsenv = baseenv_ri['.GenericArgsEnv']
#_argsenv = baseenv_ri['.ArgsEnv']
def _formals_fixed(func):
    tmp = __args(func)
    return __formals(tmp)

## docstring_property and DocstringProperty
## from Bradley Froehle
## https://gist.github.com/bfroehle/4041015
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
        l = len(obj)
        if l == 1:
            s = repr(obj[0][0])
        elif l > 1:
            s = '(%s, ...)' % repr(obj[0][0])
        else:
            s = repr(obj)
    except:
        s = repr(obj)
    return s

class Function(RObjectMixin, rinterface.SexpClosure):
    """ Python representation of an R function.
    """
    __local = baseenv_ri.get('local')
    __call = baseenv_ri.get('call')
    __assymbol = baseenv_ri.get('as.symbol')
    __newenv = baseenv_ri.get('new.env')

    _local_env = None
        
    def __init__(self, *args, **kwargs):
        super(Function, self).__init__(*args, **kwargs)
        self._local_env = self.__newenv(hash=rinterface.BoolSexpVector((True, )))

    @docstring_property(__doc__)
    def __doc__(self):
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
        new_args = [conversion.py2ri(a) for a in args]
        new_kwargs = {}
        for k, v in kwargs.items():
            new_kwargs[k] = conversion.py2ri(v)
        res = super(Function, self).__call__(*new_args, **new_kwargs)
        res = conversion.ri2ro(res)
        return res

    def formals(self):
        """ Return the signature of the underlying R function 
        (as the R function 'formals()' would).
        """
        res = _formals_fixed(self)
        res = conversion.ri2ro(res)
        return res

    def rcall(self, *args):
        """ Wrapper around the parent method rpy2.rinterface.SexpClosure.rcall(). """
        res = super(Function, self).rcall(*args)
        res = conversion.ri2ro(res)
        return res

class SignatureTranslatedFunction(Function):
    """ Python representation of an R function, where
    the character '.' is replaced with '_' in the R arguments names. """
    _prm_translate = None


    def __init__(self, sexp, init_prm_translate = None):
        super(SignatureTranslatedFunction, self).__init__(sexp)
        if init_prm_translate is None:
            prm_translate = OrderedDict()
        else:
            assert isinstance(init_prm_translate, dict)
            prm_translate = init_prm_translate

        formals = self.formals()
        if formals is not rinterface.NULL:
            for r_param in formals.names:
                py_param = r_param.replace('.', '_')
                if py_param in prm_translate:
                    raise ValueError("Error: '%s' already in the transalation table" %r_param)
                #FIXME: systematically add the parameter to the translation, as it makes it faster for generating
                # dynamically the pydoc string from the R help.
                #if py_param != r_param:
                #    prm_translate[py_param] = r_param
                prm_translate[py_param] = r_param
        self._prm_translate = prm_translate
        if hasattr(sexp, '__rname__'):
            self.__rname__ = sexp.__rname__

    @docstring_property(__doc__)
    def __doc__(self):
        doc = list(['Python representation of an R function.',
                    'R arguments:', ''])
        fm = _formals_fixed(self)
        names = fm.do_slot('names')
        for key, val in self._prm_translate.items():
            if key == '___':
                description = '(was "..."). R ellipsis (any number of parameters)'
            else:
                description = _repr_argval(fm[names.index(val)])
            doc.append('%s: %s' % (key, description))
        doc.append('')
        return os.linesep.join(doc)

    def __call__(self, *args, **kwargs):
        prm_translate = self._prm_translate
        for k in tuple(kwargs.keys()):
            r_k = prm_translate.get(k, None)
            if r_k is not None:
                v = kwargs.pop(k)
                kwargs[r_k] = v
        return super(SignatureTranslatedFunction, self).__call__(*args, **kwargs)
