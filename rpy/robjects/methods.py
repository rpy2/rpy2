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


def set_accessors(cls, cls_name, where, acs):
    # set accessors (to be moved to metaclass ?)

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
            setattr(cls, python_name, property(r_meth, None, None, docstring))
        else:
            setattr(cls, python_name, lambda self: r_meth(self))





methods_env = rinterface.baseenv.get('as.environment')(rinterface.StrSexpVector(('package:methods', )))
