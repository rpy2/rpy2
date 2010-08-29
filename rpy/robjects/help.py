""" 
R help system.

"""
import os, itertools
import rpy2.rinterface as rinterface
import conversion as conversion
import packages as packages
import rpy2.rlike.container as rlc

class Page(object):
    """ An R documentation page. 
    The original R structure is a nested sequence of components,
    corresponding to the latex-like .Rd file 

    In R the S3 class 'Rd' is the closest entity to this class.
    """

    def __init__(self, struct_rdb):
        sections = rlc.OrdDict()
        for elt in struct_rdb:
            rd_tag = elt.do_slot("Rd_tag")[0]
            if rd_tag.startswith('\\'):
                rd_tag = rd_tag[1:]
            lst = sections.get(rd_tag)
            if lst is None:
                lst = []
                sections[rd_tag] = lst
            for sub_elt in elt:
                lst.append(sub_elt)
        self.sections = sections

    def __getitem__(self, item):
        """ Get a section """
        return self.sections[item]

    def iteritems(self):
        """ iterator through the sections names and content
        in the documentation Page. """
        return self.sections.iteritems:

    def to_docstring(self, section_names = None):
        s = []

        if section_names is None:
            section_names = self.sections.keys()
            
        def walk(tree):
            if not isinstance(tree, str):
                for elt in tree:
                    walk(elt)
            else:
                s.append(tree)
                s.append(' ')

        for name in section_names:
            s.append(name)
            s.append(os.linesep)
            s.append('-' * len(name))
            s.append(os.linesep)
            s.append(os.linesep)
            walk(self.sections[name])
            s.append(os.linesep)
            s.append(os.linesep)
        return s

class Package(object):
    """ The R documentation (aka help) for a package """
    __package_path = None
    __package_name = None
    __aliases_info = 'aliases.rds'
    __paths_info = 'paths.rds'
    __anindex_info = 'AnIndex'

    def __init__(self, package_name, package_path = None):
        self.__package_name = package_name
        if package_path is None:
            package_path = packages.get_packagepath(package_name)
        self.__package_path = package_path
        #FIXME: handle the case of missing "aliases.rds"
        rpath = rinterface.StrSexpVector((os.path.join(package_path,
                                               'help',
                                               self.__aliases_info), ))
        rds = rinterface.baseenv['.readRDS'](rpath)
        rds = rinterface.StrSexpVector(rds)
        class2methods = {}
        object2alias = {}
        for k, v in itertools.izip(rds.do_slot('names'), rds):
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
        rpath = rinterface.StrSexpVector((os.path.join(package_path,
                                               'help',
                                               package_name + '.rdx'), ))
        self._rdx = conversion.ri2py(rinterface.baseenv['.readRDS'](rpath))


    def fetch(self, key):
        """ Fetch the documentation page associated with a given key. 
        
        - for S4 classes, the class name is *often* prefixed with 'class.'. For example,
        the key to the documentation for the class AnnotatedDataFrame in the package Biobase
        is 'class.AnnotatedDataFrame'.
        """
        rdx_variables = self._rdx.rx2('variables')
        if key not in rdx_variables.names:
            raise HelpNotFound("No help could be fetched", 
                               topic=key, package=self.__package_name)
        
        rkey = rinterface.StrSexpVector(rinterface.StrSexpVector((key, )))
        rpath = rinterface.StrSexpVector((os.path.join(self.package_path,
                                                       'help',
                                                       self.__package_name + '.rdb'),))
        
        _parse = rinterface.baseenv['parse']
        _eval  = rinterface.baseenv['eval']
        devnull_func = _parse(text=rinterface.StrSexpVector(('function(x) {}', )))
        devnull_func = _eval(devnull_func)
        res = rinterface.baseenv['lazyLoadDBfetch'](rdx_variables.rx(rkey)[0], 
                                                    rpath,
                                                    self._rdx.rx2("compressed"),
                                                    devnull_func)
        return conversion.ri2py(res)

    package_path = property(lambda self: str(self.__package_path),
                            None, None,
                            "Path to the installed R package")


    def __repr__(self):
        r = 'R package %s  '%self.__package_name + super(self, Package).__repr__()
        return r

class HelpNotFound(KeyError):
    def __init__(self, msg, topic=None, package=None):
        super(HelpNotFound, self).__init__(msg)
        self.topic = topic
        self.package = package
        
