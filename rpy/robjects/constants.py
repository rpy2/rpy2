import rpy2.rinterface as rinterface

_parse = rinterface.baseenv['parse']
_reval = rinterface.baseenv['eval']

# NULL
NULL = _reval(_parse(text = rinterface.StrSexpVector(("NULL", ))))
# TRUE/FALSE
TRUE = _reval(_parse(text = rinterface.StrSexpVector(("TRUE", ))))
FALSE = _reval(_parse(text = rinterface.StrSexpVector(("FALSE", ))))
