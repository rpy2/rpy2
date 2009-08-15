import rpy2.rinterface as rinterface
import rpy2.robjects.lib
import rpy2.robjects.conversion as conversion

require = rinterface.baseenv['require']
as_env = rinterface.baseenv['as.environment']

class Package(object):
    """ Models an R package
    (and can do so from an arbitrary environment - with the caution
    that locked environments should mostly be considered) """
    def __init__(self, env, name):
        """ Create a Python module-like object from an R environment """
        self._env = env
        self._name = name
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
            dot_i = rname.find('.')
            if dot_i > -1:
                rpyname = rname.replace('.', '_')
                if rpyname in self._rpy2r:
                    raise Exception('Conflict in converting R symbol ' + \
                                    'to a Python symbol' + \
                                    '(%s -> %s while there is already ' + \
                                    '%s -> %s)' %(rname, rpyname,
                                                  rname, self._rpyname))
                print('Changing ' + rname +' to ' + rpyname + \
                      ' in the package ' + name )
            else:
                rpyname = rname
            if rname in self.__dict__:
                #FIXME: raise an exception, issue a warning ?
                print('The symbol ' + rname +' in the package ' + name + \
                      ' is conflicting with a Python object attribute')
                
            self._rpy2r[rpyname] = rname
            self.__dict__[rpyname] = conversion.ri2py(self._env[rname])


class LibraryError(ImportError):
    pass


def importr(name, where = rpy2.robjects.lib):
    """ Import an R package (and return a module-like object). """
    ok = require(rinterface.StrSexpVector([name, ]))[0]
    if not ok:
        raise LibraryError("The R package %s could not be imported" %name)
    env = as_env(rinterface.StrSexpVector(['package:'+name, ]))
    pack = Package(env, name)

    if where is not None:
        if name in where.__dict__:
            raise LibraryError("An object of name %s is already found in %s" %(name, where))
        where.__dict__[name] = pack
    return pack

