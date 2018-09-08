from . import _rinterface_capi as _rinterface

_R_RPY2_MAP = {}
_R_RPY2_DEFAULT_MAP = None

_PY_RPY2_MAP = {}


def _cdata_to_rinterface(cdata):
    scaps = _rinterface.SexpCapsule(cdata)
    t = cdata.sxpinfo.type
    if t in _R_RPY2_MAP:
        cls = _R_RPY2_MAP[t]
    else:
        cls = _R_RPY2_DEFAULT_MAP
    return cls(scaps)


def _cdata_res_to_rinterface(function):
    def _(*args, **kwargs):
        cdata = function(*args, **kwargs)
        # TODO: test cdata is of of the expected CType
        return _cdata_to_rinterface(cdata)
    return _

def _python_to_cdata(obj):
    t = type(obj)
    if t in _PY_RPY2_MAP:
        cls = _PY_RPY2_MAP[t]
    else:
        raise ValueError(obj)
        # cls = _PY_RPY2_DEFAULT_MAP
    cdata = cls(obj)
    return cdata
