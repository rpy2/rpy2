""" 
R help system.

"""
import os
import rpy2.robjects as ro
import rpy2.robjects.packages as packages
ri = ro.rinterface

class Package(object):
    """ The R documentation (aka help) for a package """
    __package_path = None
    __aliases_info = 'aliases.rds'
    __paths_info = 'paths.rds'
    __anindex_info = 'AnIndex'

    def __init__(self, package_name, package_path = None):
        self.__package_name = package_name
        if package_path is None:
            package_path = packages.get_packagepath(package_name)
        self.__package_path = package_path
        #FIXME: handle the case of missing "aliases.rds"
        rpath = ri.StrSexpVector((os.path.join(package_path,
                                               'help',
                                               self.__aliases_info), ))
        rds = ri.baseenv['.readRDS'](rpath)
        rds = ro.StrVector(rds)
        class2methods = {}
        object2alias = {}
        for k, v in rds.iteritems():
            if v.startswith("class."):
                classname = v[len("class."):]
                if classname in class2methods:
                    methods = class2methods[classname]
                else:
                    methods = []
                methods.append(k.split(',')[0])
                class2methods[classname] = methods
            else:
                object2alias[v] = k

        self.class2methods = class2methods
        self.object2alias = object2alias
        rpath = ri.StrSexpVector((os.path.join(package_path,
                                               'help',
                                               package_name + '.rdx'), ))
        self._rdx = ro.Vector(ri.baseenv['.readRDS'](rpath))


    def fetch(self, key):
        """ Fetch the documentation associated with a given key. """
        rdx_variables = self._rdx.rx2('variables')
        assert key in rdx_variables.names
        
        rkey = ri.StrSexpVector(ri.StrSexpVector((key, )))
        rpath = ri.StrSexpVector((os.path.join(self.package_path,
                                               'help',
                                               self.__package_name + '.rdb'),))

        res = ri.baseenv['lazyLoadDBfetch'](rdx_variables.rx(rkey)[0], 
                                            rpath,
                                            self._rdx.rx2("compressed"),
                                            ro.r('function(x) {}'))
        return ro.Vector(res)

    package_path = property(lambda self: str(self.__package_path),
                            None, None,
                            "Path to the installed R package")




