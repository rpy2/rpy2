import rpy2.rinterface as rinterface
import rpy2.robjects.lib
import rpy2.robjects.conversion as conversion
from rpy2.robjects import Function
from rpy2.robjects import NULL

_require = rinterface.baseenv['require']
_as_env = rinterface.baseenv['as.environment']


class Package(object):
    """ Models an R package
    (and can do so from an arbitrary environment - with the caution
    that locked environments should mostly be considered) """
    
    def __init__(self, env, name, translation = {}):
        """ Create a Python module-like object from an R environment,
        using the specified translation if defined. """
        self._env = env
        self._name = name
        self._translation = translation
        mynames = tuple(self.__dict__)
        self._rpy2r = {}
        self.__fill_rpy2r__()
        self.__update_dict__()

    def __update_dict__(self):
        """ Update the __dict__ according to what is in the R environment """
        for elt in self._rpy2r:
            del(self.__dict__[elt])
        self._rpy2r = {}
        self.__fill_rpy2r__()

    def __fill_rpy2r__(self):
        """ Fill the attribute _rpy2r """
        name = self._name
        for rname in self._env:
            if rname in self._translation:
                rpyname = self._translation[rname]
            else:
                dot_i = rname.find('.')
                if dot_i > -1:
                    rpyname = rname.replace('.', '_')
                    if rpyname in self._rpy2r:
                        raise LibraryError(('Conflict in converting R symbol'+\
                                            ' to a Python symbol ' +\
                                            '(%s -> %s while there is already'+\
                                            ' %s)') %(rname, rpyname,
                                                      rpyname))
                else:
                    rpyname = rname
                if rpyname in self.__dict__ or rpyname == '__dict__':
                    raise LibraryError('The symbol ' + rname +\
                                       ' in the package ' + name + \
                                       ' is conflicting with ' +\
                                       'a Python object attribute')
            self._rpy2r[rpyname] = rname
            rpyobj = conversion.ri2py(self._env[rname])
            #FIXME: shouldn't the original R name be also in the __dict__ ?
            self.__dict__[rpyname] = rpyobj



class SignatureTranslatedFunction(Function):
    """ Wraps an R function in such way that the R argument names with the
    character '.' are replaced with '_' whenever present """
    _prm_translate = None

    def __init__(self, *args):
        super(SignatureTranslatedFunction, self).__init__(*args)
        prm_translate = {}
        if not self.formals().rsame(NULL):
            for r_param in self.formals().names:
                py_param = r_param.replace('.', '_')
                if py_param in prm_translate:
                    raise ValueError("Error: '%s' already in the transalation table" %r_param)
                if py_param != r_param:
                    prm_translate[py_param] = r_param
        self._prm_translate = prm_translate

    def __call__(self, *args, **kwargs):
        prm_translate = self._prm_translate
        for k in tuple(kwargs.keys()):
            r_k = prm_translate.get(k, None)
            if r_k is not None:
                v = kwargs.pop(k)
                kwargs[r_k] = v
        return super(SignatureTranslatedFunction, self).__call__(*args, **kwargs)

class SignatureTranslatedPackage(Package):
    def __fill_rpy2r__(self):
        super(SignatureTranslatedPackage, self).__fill_rpy2r__()
        for name, robj in self.__dict__.iteritems():
            if isinstance(robj, rinterface.Sexp) and robj.typeof == rinterface.CLOSXP:
                self.__dict__[name] = SignatureTranslatedFunction(self.__dict__[name])


class LibraryError(ImportError):
    """ Error occuring when importing an R library """
    pass


def importr(name, robject_translations = {}, signature_translation = True):
    """ Import an R package (and return a module-like object). """
    ok = _require(rinterface.StrSexpVector([name, ]))[0]
    if not ok:
        raise LibraryError("The R package %s could not be imported" %name)
    env = _as_env(rinterface.StrSexpVector(['package:'+name, ]))
    if signature_translation:
        pack = SignatureTranslatedPackage(env, name, 
                                          translation = robject_translations)
    else:
        pack = Package(env, name, translation = robject_translations)
        
    return pack


def wherefrom(symbol, startenv = rinterface.globalenv):
    """ For a given symbol, return the environment
    this symbol is first found in, starting from 'startenv'
    """
    env = startenv
    obj = None
    tryagain = True
    while tryagain:
        try:
            obj = env[symbol]
            tryagain = False
        except LookupError, knf:
            env = env.enclos()
            if env.rsame(rinterface.emptyenv):
                tryagain = False
            else:
                tryagain = True
    return conversion.ri2py(env)
