import rpy2.robjects. as robjects
import rpy2.rinterface as rinterface

getmethod = robjects.baseNameSpaceEnv.get("getMethod")

require = robjects.baseNameSpaceEnv.get('require')
require('methods', quiet = True)

methods_env = robjects.baseNameSpaceEnv['as.environment']('package:methods')

class RS4(robjects.RObjectMixin, rinterface.SexpS4):

    def slotnames(self):
        return methods_env['slotNames']()

    
    @staticmethod
    def isclass(name):
        return methods_env['isClass'](name)


    def validobject(self, test = False, complete = False):
        return methods_env['validObject'](test = False, complete = False)
