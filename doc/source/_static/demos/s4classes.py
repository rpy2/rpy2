
#-- setup-begin
import rpy2.robjects as robjects
import rpy2.rinterface as rinterface
from rpy2.robjects.packages import importr

lme4 = importr("lme4")
getmethod = robjects.baseenv.get("getMethod")

StrVector = robjects.StrVector
#-- setup-end

#-- LmList-begin
class LmList(robjects.methods.RS4):
    """ Reflection of the S4 class 'lmList'. """
    
    _coef = getmethod("coef", 
                      signature = StrVector(["lmList", ]),
                      where = "package:lme4")
    _confint = getmethod("confint", 
                         signature = StrVector(["lmList", ]),
                         where = "package:lme4")
    _formula = getmethod("formula", 
                         signature = StrVector(["lmList", ]),
                         where = "package:lme4")
    _lmfit_from_formula = getmethod("lmList",
                                    signature = StrVector(["formula", "data.frame"]),
                                    where = "package:lme4")

    def _call_get(self):
        return self.do_slot("call")
    def _call_set(self, value):
        return self.do_slot("call", value)
    call = property(_call_get, _call_set, None, "Get or set the RS4 slot 'call'.")

    def coef(self):
        """ fitted coefficients """
        return self._coef(self)
    
    def confint(self):
        """ confidence interval """
        return self._confint(self)
    
    def formula(self):
        """ formula used to fit the model """
        return self._formula(self)
    
    @staticmethod
    def from_formula(formula, 
                     data = rinterface.MissingArg,
                     family = rinterface.MissingArg,
                     subset = rinterface.MissingArg,
                     weights = rinterface.MissingArg):
        """ Build an LmList from a formula """
        res = LmList._lmfit_from_formula(formula, data,
                                         family = family,
                                         subset = subset,
                                         weights = weights)
        res = LmList(res)
        return res
#-- LmList-end

#-- buildLmList-begin
sleepstudy = lme4.sleepstudy
formula = robjects.Formula('Reaction ~ Days | Subject')
lml1 = LmList.from_formula(formula, 
                           sleepstudy)
#-- buildLmList-end


#-- buildLmListBetterCall-begin
sleepstudy = lme4.sleepstudy
formula = robjects.Formula('Reaction ~ Days | Subject')
for varname in ('Reaction', 'Days', 'Subject'):
    formula.environment[varname] = sleepstudy.rx2(varname)

lml1 = LmList.from_formula(formula)
#-- buildLmListBetterCall-end

