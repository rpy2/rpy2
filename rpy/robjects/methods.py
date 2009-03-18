from rpy2.robjects.robject import RObjectMixin
import rpy2.rinterface as rinterface

class RS4(RObjectMixin, rinterface.SexpS4):
    pass
