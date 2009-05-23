from rpy2.robjects.robject import RObjectMixin
import rpy2.rinterface as rinterface
import conversion

getmethod = rinterface.baseenv.get("getMethod")

require = rinterface.baseenv.get('require')
require(rinterface.StrSexpVector(('methods', )),
        quiet = rinterface.BoolSexpVector((True, )))


class RS4(RObjectMixin, rinterface.SexpS4):

    def slotnames(self):
        return methods_env['slotNames'](self)

    
    @staticmethod
    def isclass(name):
        return methods_env['isClass'](name)


    def validobject(self, test = False, complete = False):
        return methods_env['validObject'](test = False, complete = False)


class RS4_Type(type):
    def __new__(mcs, name, bases, cls_dict):

        cls_rname = cls_dict['__rname__']
        for rname, where, \
                python_name, as_property, \
                docstring in cls_dict['__accessors__']:

            if where is None:
                where = rinterface.globalenv
            else:
                where = "package:" + str(where)
                where = rinterface.StrSexpVector((where, ))

            if python_name is None:
                python_name = r_name
                
            signature = rinterface.StrSexpVector((cls_rname, ))            
            r_meth = getmethod(rinterface.StrSexpVector((rname, )), 
                               signature = signature,
                               where = where)
            r_meth = conversion.ri2py(r_meth)
            if as_property:
                cls_dict[python_name] = property(r_meth, None, None)
            else:
                cls_dict[python_name] =  lambda self: r_meth(self)
                
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
