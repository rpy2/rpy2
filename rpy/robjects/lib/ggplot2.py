import rpy2.robjects.methods
import rpy2.robjects as robjects
import rpy2.robjects.conversion as conversion

import copy

#getmethod = robjects.baseenv.get("getMethod")

rimport = robjects.baseenv.get('library')
rimport('ggplot2')

ggplot2_env = robjects.baseenv['as.environment']('package:ggplot2')

StrVector = robjects.StrVector

def as_symbol(x):
   res = robjects.baseenv["parse"](text = x)
   return res


class GGPlot(robjects.RObject):

    _constructor = ggplot2_env['ggplot']
    _rprint = ggplot2_env['print.ggplot']
    _add = ggplot2_env['+.ggplot']

    @classmethod
    def new(cls, data):
        res = cls(cls._constructor(data))
        return res
    
    def plot(self):
        self._rprint(self)

    def __add__(self, obj):
        res = self._add(self, obj)
        return res



class Aes(robjects.RVector):
    _constructor = ggplot2_env['aes_string']
    #_constructor = ggplot2_env['aes']
    
    @classmethod
    def new(cls, **kwargs):
       new_kwargs = copy.copy(kwargs)
       for k,v in kwargs.iteritems():
          new_kwargs[k] = as_symbol(v)
       res = cls(cls._constructor(**new_kwargs))
       return res


class Layer(robjects.RObject):
    _constructor = ggplot2_env['layer']
    #_dollar = proto_env["$.proto"]

    @classmethod
    def new(cls,
            geom, geom_params,
            stat, stat_params,
            data,
            aesthetics,
            position,
            params):

        args = [conversion.py2ro(x) for x in (geom, geom_params,
                                              stat, stat_params,
                                              data,
                                              aesthetics,
                                              position,
                                              params)]

        res = cls(cls.contructor)(*args)
        return res
        

class GBaseObject(robjects.RObject):
    @classmethod
    def new(*args, **kwargs):
       args_list = list(args)
       cls = args_list.pop(0)
       res = cls(cls._constructor(*args_list, **kwargs))
       return res

class Stat(GBaseObject):
   pass

class StatAbline(Stat):
   _constructor = ggplot2_env['stat_abline']
class StatBin(Stat):
   _constructor = ggplot2_env['stat_bin']
class StatBin2D(Stat):
   _constructor = ggplot2_env['stat_bin2d']
class StatBinhex(Stat):
   _constructor = ggplot2_env['stat_binhex']
class StatBoxplot(Stat):
   _constructor = ggplot2_env['stat_boxplot']
class StatContour(Stat):
   _constructor = ggplot2_env['stat_contour']
class StatDensity(Stat):
   _constructor = ggplot2_env['stat_density']
class StatDensity2D(Stat):
   _constructor = ggplot2_env['stat_density2d']
class StatFunction(Stat):
   _constructor = ggplot2_env['stat_function']
class StatHline(Stat):
   _constructor = ggplot2_env['stat_hline']
class StatIdentity(Stat):
   _constructor = ggplot2_env['stat_identity']
class StatQq(Stat):
   _constructor = ggplot2_env['stat_qq']
class StatQuantile(Stat):
   _constructor = ggplot2_env['stat_quantile']
class StatSmooth(Stat):
   _constructor = ggplot2_env['stat_smooth']
class StatSpoke(Stat):
   _constructor = ggplot2_env['stat_spoke']
class StatSum(Stat):
   _constructor = ggplot2_env['stat_sum']
class StatSummary(Stat):
   _constructor = ggplot2_env['stat_summary']
class StatUnique(Stat):
   _constructor = ggplot2_env['stat_unique']
class StatVline(Stat):
   _constructor = ggplot2_env['stat_vline']


class Coord(GBaseObject):
   pass

class CoordCartesian(Coord):
   _constructor = ggplot2_env['coord_cartesian']
class CoordEqual(Coord):
   _constructor = ggplot2_env['coord_equal']
class CoordFlip(Coord):
   _constructor = ggplot2_env['coord_flip']
class CoordMap(Coord):
   _constructor = ggplot2_env['coord_map']
class CoordPolar(Coord):
   _constructor = ggplot2_env['coord_polar']
class CoordTrans(Coord):
   _constructor = ggplot2_env['coord_trans']

class Facet(GBaseObject):
   pass

class FacetGrid(Facet):
   _constructor = ggplot2_env['facet_grid']
class FacetWrap(Facet):
   _constructor = ggplot2_env['facet_wrap']


class Geom(GBaseObject):
    pass

class GeomAbline(Geom):
   _constructor = ggplot2_env['geom_abline']
class GeomArea(Geom):
   _constructor = ggplot2_env['geom_area']
class GeomBar(Geom):
   _constructor = ggplot2_env['geom_bar']
class GeomBin2D(Geom):
   _constructor = ggplot2_env['geom_bin2d']
class GeomBlank(Geom):
   _constructor = ggplot2_env['geom_blank']
class GeomBoxplot(Geom):
   _constructor = ggplot2_env['geom_boxplot']
class GeomContour(Geom):
   _constructor = ggplot2_env['geom_contour']
class GeomCrossBar(Geom):
   _constructor = ggplot2_env['geom_crossbar']
class GeomDensity(Geom):
   _constructor = ggplot2_env['geom_density']
class GeomDensity2D(Geom):
   _constructor = ggplot2_env['geom_density2d']
class GeomErrorBar(Geom):
   _constructor = ggplot2_env['geom_errorbar']
class GeomErrorBarH(Geom):
   _constructor = ggplot2_env['geom_errorbarh']
class GeomFreqPoly(Geom):
   _constructor = ggplot2_env['geom_freqpoly']
class GeomHex(Geom):
   _constructor = ggplot2_env['geom_histogram']
class GeomHistogram(Geom):
   _constructor = ggplot2_env['geom_histogram']
class GeomHLine(Geom):
   _constructor = ggplot2_env['geom_hline']
class GeomJitter(Geom):
   _constructor = ggplot2_env['geom_jitter']
class GeomLine(Geom):
   _constructor = ggplot2_env['geom_line']
class GeomLineRange(Geom):
   _constructor = ggplot2_env['geom_linerange']
class GeomPath(Geom):
   _constructor = ggplot2_env['geom_path']
class GeomPoint(Geom):
   _constructor = ggplot2_env['geom_point']
class GeomPointRange(Geom):
   _constructor = ggplot2_env['geom_pointrange']
class GeomPolygon(Geom):
   _constructor = ggplot2_env['geom_polygon']
class GeomQuantile(Geom):
   _constructor = ggplot2_env['geom_quantile']
class GeomRect(Geom):
   _constructor = ggplot2_env['geom_rect']
class GeomRibbon(Geom):
   _constructor = ggplot2_env['geom_ribbon']
class GeomRug(Geom):
   _constructor = ggplot2_env['geom_rug']
class GeomSegment(Geom):
   _constructor = ggplot2_env['geom_segment']
class GeomSmooth(Geom):
   _constructor = ggplot2_env['geom_smooth']
class GeomStep(Geom):
   _constructor = ggplot2_env['geom_step']
class GeomText(Geom):
   _constructor = ggplot2_env['geom_text']
class GeomTile(Geom):
   _constructor = ggplot2_env['geom_tile']
class GeomVLine(Geom):
   _constructor = ggplot2_env['geom_vline']


class Position(GBaseObject):
   pass

class PositionDodge(Position):
   _constructor = ggplot2_env['position_dodge']
class PositionFill(Position):
   _constructor = ggplot2_env['position_fill']
class PositionIdentify(Position):
   _constructor = ggplot2_env['position_identity']
class PositionJitter(Position):
   _constructor = ggplot2_env['position_jitter']
class PositionStack(Position):
   _constructor = ggplot2_env['position_stack']


class Scale(GBaseObject):
   pass

class ScaleAlpha(Scale):
   _constructor = ggplot2_env['scale_alpha']
#class ScaleBrewer(Scale):
#   _constructor = ggplot2_env['scale_brewer']
class ScaleColour(Scale):
   _constructor = ggplot2_env['scale_colour']
#class ScaleContinuous(Scale):
#   _constructor = ggplot2_env['scale_continuous']
# class ScaleDate(Scale):
#    _constructor = ggplot2_env['scale_date']
# class ScaleDateTime(Scale):
#    _constructor = ggplot2_env['scale_datetime']
class ScaleDiscrete(Scale):
   _constructor = ggplot2_env['scale_discrete']
# class ScaleGradient(Scale):
#    _constructor = ggplot2_env['scale_gradient']
# class ScaleGradient2(Scale):
#    _constructor = ggplot2_env['scale_gradient2']
# class ScaleGradientN(Scale):
#    _constructor = ggplot2_env['scale_gradientn']
# class ScaleGrey(Scale):
#    _constructor = ggplot2_env['scale_grey']
# class ScaleHue(Scale):
#    _constructor = ggplot2_env['scale_hue']
# class ScaleIdentity(Scale):
#    _constructor = ggplot2_env['scale_identity']
class Scalelinetype(Scale):
   _constructor = ggplot2_env['scale_linetype']
# class ScaleManual(Scale):
#    _constructor = ggplot2_env['scale_manual']
class ScaleShape(Scale):
   _constructor = ggplot2_env['scale_shape']
class ScaleSize(Scale):
   _constructor = ggplot2_env['scale_size']
# class ScaleList(Scale):
#    _constructor = ggplot2_env['scale_list']


class ScaleX(Scale):
   pass
class ScaleY(Scale):
   pass

class ScaleXContinuous(ScaleX):
   _constructor = ggplot2_env['scale_x_continuous']
class ScaleYContinuous(ScaleY):
   _constructor = ggplot2_env['scale_y_continuous']
class ScaleXDiscrete(ScaleX):
   _constructor = ggplot2_env['scale_x_discrete']
class ScaleYDiscrete(ScaleY):
   _constructor = ggplot2_env['scale_y_discrete']
class ScaleXDate(ScaleX):
   _constructor = ggplot2_env['scale_x_date']
class ScaleYDate(ScaleY):
   _constructor = ggplot2_env['scale_y_date']
class ScaleXDatetime(ScaleX):
   _constructor = ggplot2_env['scale_x_datetime']
class ScaleYDatetime(ScaleY):
   _constructor = ggplot2_env['scale_y_datetime']
class ScaleXExp(ScaleX):
   _constructor = ggplot2_env['scale_x_exp']
class ScaleYExp(ScaleY):
   _constructor = ggplot2_env['scale_y_exp']
class ScaleXInverse(ScaleX):
   _constructor = ggplot2_env['scale_x_inverse']
class ScaleYInverse(ScaleY):
   _constructor = ggplot2_env['scale_y_inverse']
class ScaleXLog(ScaleX):
   _constructor = ggplot2_env['scale_x_log']
class ScaleYLog(ScaleY):
   _constructor = ggplot2_env['scale_y_log']
class ScaleXLog10(ScaleX):
   _constructor = ggplot2_env['scale_x_log10']
class ScaleYLog10(ScaleY):
   _constructor = ggplot2_env['scale_y_log10']
class ScaleXLog2(ScaleX):
   _constructor = ggplot2_env['scale_x_log2']
class ScaleYLog2(ScaleY):
   _constructor = ggplot2_env['scale_y_log2']
class ScaleXLogit(ScaleX):
   _constructor = ggplot2_env['scale_x_logit']
class ScaleYLogit(ScaleY):
   _constructor = ggplot2_env['scale_y_logit']
class ScaleXPow(ScaleX):
   _constructor = ggplot2_env['scale_x_pow']
class ScaleYPow(ScaleY):
   _constructor = ggplot2_env['scale_y_pow']
class ScaleXPow10(ScaleX):
   _constructor = ggplot2_env['scale_x_pow10']
class ScaleYPow10(ScaleY):
   _constructor = ggplot2_env['scale_y_pow10']
class ScaleXProb(ScaleX):
   _constructor = ggplot2_env['scale_x_prob']
class ScaleYProb(ScaleY):
   _constructor = ggplot2_env['scale_y_prob']
class ScaleXProbit(ScaleX):
   _constructor = ggplot2_env['scale_x_probit']
class ScaleYProbit(ScaleY):
   _constructor = ggplot2_env['scale_y_probit']
class ScaleXReverse(ScaleX):
   _constructor = ggplot2_env['scale_x_reverse']
class ScaleYReverse(ScaleY):
   _constructor = ggplot2_env['scale_y_reverse']
class ScaleXSqrt(ScaleX):
   _constructor = ggplot2_env['scale_x_sqrt']
class ScaleYSqrt(ScaleY):
   _constructor = ggplot2_env['scale_y_sqrt']

class ScaleColourBrewer(ScaleColour):
   _constructor = ggplot2_env['scale_colour_brewer']
class ScaleColourGradient(ScaleColour):
   _constructor = ggplot2_env['scale_colour_gradient']
class ScaleColourGradient2(ScaleColour):
   _constructor = ggplot2_env['scale_colour_gradient2']
class ScaleColourGrey(ScaleColour):
   _constructor = ggplot2_env['scale_colour_grey']


opts = ggplot2_env['opts']

original_conversion = conversion.ri2py
def ggplot2_conversion(robj):

    pyobj = original_conversion(robj)

    if 'ggplot' in pyobj.rclass:
       pyobj = GGPlot(pyobj)

    return pyobj

conversion.ri2py = ggplot2_conversion

