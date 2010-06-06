from rpy2.robjects.robject import RObjectMixin
import rpy2.rinterface as rinterface
import conversion

getmethod = rinterface.baseenv.get("getMethod")

require = rinterface.baseenv.get('require')
require(rinterface.StrSexpVector(('methods', )),
        quiet = rinterface.BoolSexpVector((True, )))


class RS4(RObjectMixin, rinterface.SexpS4):
    """ Python representation of an R instance of class 'S4'. """

    def slotnames(self):
        """ Return the 'slots' defined for this object """
        return methods_env['slotNames'](self)
    
    def do_slot(self, name):
        return conversion.ri2py(super(RS4, self).do_slot(name))

    @staticmethod
    def isclass(name):
        """ Return whether the given name is a defined class. """
        name = conversion.py2ri(name)
        return methods_env['isClass'](name)[0]

    def validobject(self, test = False, complete = False):
        """ Return whether the instance is 'valid' for its class. """
        test = conversion.py2ri(test)
        complete = conversion.py2ri(complete)
        return methods_env['validObject'](self, test = test,
                                          complete = complete)[0]

class ClassRepresentation(RS4):
    """ """
    slots = property(lambda x: [y[0] for y in x.do_slot('slots')],
                     None, None,
                     "Slots (attributes) for the class")
    basenames = property(lambda x: [y[0] for y in x.do_slot('contains')],
                     None, None,
                     "parent classes")
    contains = basenames
    isabstract = property(lambda x: x.do_slot('virtual')[0],
                          None, None,
                          "Is the class an abstract class ?")
    virtual = isabstract
    packagename = property(lambda x: x.do_slot('package')[0],
                           None, None,
                           "R package in which the class is defined")
    package = packagename
    classname = property(lambda x: x.do_slot('className')[0],
                         None, None,
                         "Name of the R class")

def getclassdef(cls_name, cls_package):
    cls_def = methods_env['getClassDef'](rinterface.StrSexpVector((cls_name,)),
                                         rinterface.StrSexpVector((cls_package, )))
    cls_def = ClassRepresentation(cls_def)
    return cls_def

class RS4_Type(type):
    def __new__(mcs, name, bases, cls_dict):

        try:
            cls_rname = cls_dict['__rname__']
        except KeyError, ke:
            cls_rname = name

        try:
            accessors = cls_dict['__accessors__']
        except KeyError, ke:
            accessors = []
            
        for rname, where, \
                python_name, as_property, \
                docstring in accessors:

            if where is None:
                where = rinterface.globalenv
            else:
                where = "package:" + str(where)
                where = rinterface.StrSexpVector((where, ))

            if python_name is None:
                python_name = rname
                
            signature = rinterface.StrSexpVector((cls_rname, ))            
            r_meth = getmethod(rinterface.StrSexpVector((rname, )), 
                               signature = signature,
                               where = where)
            r_meth = conversion.ri2py(r_meth)
            if as_property:
                cls_dict[python_name] = property(r_meth, None, None,
                                                 doc = docstring)
            else:
                cls_dict[python_name] =  lambda self: r_meth(self)
                
        return type.__new__(mcs, name, bases, cls_dict)

# playground to experiment with more metaclass-level automation
class RS4Auto_Type(type):
    def __new__(mcs, name, bases, cls_dict):
        try:
            cls_rname = cls_dict['__rname__']
        except KeyError, ke:
            cls_rname = name

        try:
            cls_rpackage = cls_dict['__rpackage__']
        except KeyError, ke:
            cls_rpackage = globalenv

        cls_def = getclassdef(cls_name, cls_package)
    
        # documentation
        
        for slt_name in cls_def.slots:
            cls_dict[slt_name] = property(lambda self: self.do_slot(slt_name),
                                          None, None,
                                          )

            # if where is None:
            #     where = rinterface.globalenv
            # else:
            #     where = "package:" + cls_def.packagename
            #     where = rinterface.StrSexpVector((where, ))

            # if python_name is None:
            #     python_name = rname
                
            # signature = rinterface.StrSexpVector((cls_rname, ))            
            # r_meth = getmethod(rinterface.StrSexpVector((rname, )), 
            #                    signature = signature,
            #                    where = where)
            # r_meth = conversion.ri2py(r_meth)
            # if as_property:
            #     cls_dict[python_name] = property(r_meth, None, None,
            #                                      doc = docstring)
            # else:
            #     cls_dict[python_name] =  lambda self: r_meth(self)
                
        return type.__new__(mcs, name, bases, cls_dict)


def set_accessors(cls, cls_name, where, acs):
    # set accessors (to be abandonned for the metaclass above ?)

    if where is None:
        where = rinterface.globalenv
    else:
        where = "package:" + str(where)
        where = rinterface.StrSexpVector((where, ))

    for r_name, python_name, as_property, docstring in acs:
        if python_name is None:
            python_name = r_name
        r_meth = getmethod(rinterface.StrSexpVector((r_name, )), 
                           signature = rinterface.StrSexpVector((cls_name, )),
                           where = where)
        r_meth = conversion.ri2py(r_meth)
        if as_property:
            setattr(cls, python_name, property(r_meth, None, None))
        else:
            setattr(cls, python_name, lambda self: r_meth(self))





methods_env = rinterface.baseenv.get('as.environment')(rinterface.StrSexpVector(('package:methods', )))
