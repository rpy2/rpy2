
#-- setup-begin
import rpy2.robjects as robjects
import rpy2.rinterface as rinterface
from rpy2.robjects.packages import importr, data
from rpy2.robjects.methods import getmethod

lme4 = importr('lme4')
utils = importr('utils')

StrVector = robjects.StrVector
#-- setup-end

#-- LmList-begin
class LmList(robjects.methods.RS4):
    """ Reflection of the S4 class 'lmList'. """
    
    _coef = utils.getS3method(
        'coef', 
        'lmList4')
    _confint = utils.getS3method(
        'confint', 
        'lmList4')
    _formula = utils.getS3method(
        'formula', 
        'lmList4')
    _lmfit_from_formula = staticmethod(lme4.lmList)

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
                     data=rinterface.MissingArg,
                     family=rinterface.MissingArg,
                     subset=rinterface.MissingArg,
                     weights=rinterface.MissingArg):
        """ Build an LmList from a formula """
        res = LmList._lmfit_from_formula(formula,
                                         data=data,
                                         family=family,
                                         subset=subset,
                                         weights=weights)
        res = LmList(res)
        return res
#-- LmList-end

#-- buildLmList-begin
sleepstudy = data(lme4).fetch('sleepstudy')['sleepstudy']
formula = robjects.Formula('Reaction ~ Days | Subject')
lml1 = LmList.from_formula(formula, 
                           data=sleepstudy)
#-- buildLmList-end


#-- buildLmListBetterCall-begin
sleepstudy = data(lme4).fetch('sleepstudy')['sleepstudy']
formula = robjects.Formula('Reaction ~ Days | Subject')

lml1 = LmList.from_formula(formula,
                           data=sleepstudy)
#-- buildLmListBetterCall-end

