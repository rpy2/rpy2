import os
import sys
import rpy2.rinterface as rinterface

rinterface.initr()

class RObjectMixin(object):
    """ Class to provide methods common to all RObject instances """
    name = None

    __tempfile = rinterface.baseNameSpaceEnv.get("tempfile")
    __file = rinterface.baseNameSpaceEnv.get("file")
    __fifo = rinterface.baseNameSpaceEnv.get("fifo")
    __sink = rinterface.baseNameSpaceEnv.get("sink")
    __close = rinterface.baseNameSpaceEnv.get("close")
    __readlines = rinterface.baseNameSpaceEnv.get("readLines")
    __unlink = rinterface.baseNameSpaceEnv.get("unlink")
    __rclass = rinterface.baseNameSpaceEnv.get("class")
    __show = rinterface.baseNameSpaceEnv.get("show")

    def __str__(self):
        if sys.platform == 'win32':
            tfile = self.__tempfile()
            tmp = self.__file(tfile, open = rinterface.StrSexpVector(["w", ]))
        else:
            tmp = self.__fifo(rinterface.StrSexpVector(["", ]))
        self.__sink(tmp)
        self.__show(self)
        self.__sink()
        if sys.platform == 'win32':
            self.__close(tmp)
            tmp = self.__file(tfile, open = rinterface.StrSexpVector(["r", ]))
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
        return self.__rclass(self)

    rclass = property(getrclass)


def repr_robject(o, linesep=os.linesep):
    s = rinterface.baseNameSpaceEnv.get("deparse")(o)
    s = str.join(linesep, s)
    return s



class RObject(RObjectMixin, rinterface.Sexp):
    """ Base class for all R objects. """
    def __setattr__(self, name, value):
        if name == '_sexp':
            if not isinstance(value, rinterface.Sexp):
                raise ValueError("_attr must contain an object " +\
                                     "that inherits from rinterface.Sexp" +\
                                     "(not from %s)" %type(value))
        super(RObject, self).__setattr__(name, value)
