from rpy2.robjects.robject import RObjectMixin
import rpy2.rinterface as rinterface

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



methods_env = rinterface.baseenv.get('as.environment')(rinterface.StrSexpVector(('package:methods', )))
