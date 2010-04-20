import rpy2.rinterface as rinterface
import rpy2.robjects.lib
import rpy2.robjects.conversion as conversion
from rpy2.robjects.functions import SignatureTranslatedFunction
from rpy2.robjects import NULL

_require = rinterface.baseenv['require']
_as_env = rinterface.baseenv['as.environment']

def quiet_require(name, lib_loc = None):
    _parse = rinterface.baseenv['parse']
    if lib_loc == None:
        lib_loc = "NULL"
    expr_txt = "suppressPackageStartupMessages(base::require(%s, lib.loc=%s))" \
        %(name, lib_loc)
    expr = _parse(text = rinterface.StrSexpVector([expr_txt, ]))
    ok = rinterface.baseenv['eval'](expr)
    return ok

class Package(object):
    """ Models an R package
    (and can do so from an arbitrary environment - with the caution
    that locked environments should mostly be considered).
     """
    
    def __init__(self, env, name, translation = {}):
        """ Create a Python module-like object from an R environment,
        using the specified translation if defined. """
        self._env = env
        self.__rname__ = name
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
        name = self.__rname__
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
            rpyobj.__rname__ = rname
            #FIXME: shouldn't the original R name be also in the __dict__ ?
            self.__dict__[rpyname] = rpyobj



class SignatureTranslatedPackage(Package):
    def __fill_rpy2r__(self):
        super(SignatureTranslatedPackage, self).__fill_rpy2r__()
        for name, robj in self.__dict__.iteritems():
            if isinstance(robj, rinterface.Sexp) and robj.typeof == rinterface.CLOSXP:
                self.__dict__[name] = SignatureTranslatedFunction(self.__dict__[name])


class LibraryError(ImportError):
    """ Error occuring when importing an R library """
    pass



def importr(name, 
            lib_loc = None,
            robject_translations = {}, signature_translation = True,
            suppress_messages = True):
    """ Import an R package (and return a module-like object). """
    if suppress_messages:
        ok = quiet_require(name, lib_loc = lib_loc)
    else:
        ok = _require(rinterface.StrSexpVector([name, ]), **{'lib.loc': lib_loc})[0]
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
