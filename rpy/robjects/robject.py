import os
import sys
import rpy2.rinterface

rpy2.rinterface.initr()

import conversion

class RObjectMixin(object):
    """ Class to provide methods common to all RObject instances """
    name = None

    __tempfile = rpy2.rinterface.baseenv.get("tempfile")
    __file = rpy2.rinterface.baseenv.get("file")
    __fifo = rpy2.rinterface.baseenv.get("fifo")
    __sink = rpy2.rinterface.baseenv.get("sink")
    __close = rpy2.rinterface.baseenv.get("close")
    __readlines = rpy2.rinterface.baseenv.get("readLines")
    __unlink = rpy2.rinterface.baseenv.get("unlink")
    __rclass = rpy2.rinterface.baseenv.get("class")
    __show = rpy2.rinterface.baseenv.get("show")

    def __str__(self):
        if sys.platform == 'win32':
            tfile = self.__tempfile()
            tmp = self.__file(tfile, open = rpy2.rinterface.StrSexpVector(["w", ]))
        else:
            tmp = self.__fifo(rpy2.rinterface.StrSexpVector(["", ]))
        self.__sink(tmp)
        self.__show(self)
        self.__sink()
        if sys.platform == 'win32':
            self.__close(tmp)
            tmp = self.__file(tfile, open = rpy2.rinterface.StrSexpVector(["r", ]))
        s = self.__readlines(tmp)
        if sys.platform == 'win32':
            self.__unlink(tfile)
        else:
            self.__close(tmp)
        s = str.join(os.linesep, s)
        return s

    def r_repr(self):
        """ R string representation for an object.
        This string representation can be used directed
        in R code.
        """
        return repr_robject(self, linesep='\n')

    def getrclass(self):
        """ Return the name of the R class for the object. """
        try:
            return self.__rclass(self)
        except rpy2.rinterface.RRuntimeError, rre:
            if self.typeof == rpy2.rinterface.SYMSXP:
                #unevaluated expression: has no class
                return (None, )
            else:
                raise rre
            
    rclass = property(getrclass)


def repr_robject(o, linesep=os.linesep):
    s = rpy2.rinterface.baseenv.get("deparse")(o)
    s = str.join(linesep, s)
    return s



class RObject(RObjectMixin, rpy2.rinterface.Sexp):
    """ Base class for all R objects. """
    def __setattr__(self, name, value):
        if name == '_sexp':
            if not isinstance(value, rpy2.rinterface.Sexp):
                raise ValueError("_attr must contain an object " +\
                                     "that inherits from rpy2.rinterface.Sexp" +\
                                     "(not from %s)" %type(value))
        super(RObject, self).__setattr__(name, value)

