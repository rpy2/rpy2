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

ggplot = GGPlot.new


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
aes = Aes.new

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
layer = Layer.new        

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
stat_abline = StatAbline.new

class StatBin(Stat):
   _constructor = ggplot2_env['stat_bin']
stat_bin = StatBin.new

class StatBin2D(Stat):
   _constructor = ggplot2_env['stat_bin2d']
stat_bin2d = StatBin2D.new

class StatBinhex(Stat):
   _constructor = ggplot2_env['stat_binhex']
stat_binhex = StatBinhex.new
   
class StatBoxplot(Stat):
   _constructor = ggplot2_env['stat_boxplot']
stat_boxplot = StatBoxplot.new

class StatContour(Stat):
   _constructor = ggplot2_env['stat_contour']
stat_contour = StatContour.new

class StatDensity(Stat):
   _constructor = ggplot2_env['stat_density']
stat_density = StatDensity.new

class StatDensity2D(Stat):
   _constructor = ggplot2_env['stat_density2d']
stat_density2d = StatDensity2D.new

class StatFunction(Stat):
   _constructor = ggplot2_env['stat_function']
stat_function = StatFunction.new

class StatHline(Stat):
   _constructor = ggplot2_env['stat_hline']
stat_hline = StatHline.new

class StatIdentity(Stat):
   _constructor = ggplot2_env['stat_identity']
stat_identity = StatIdentity.new

class StatQQ(Stat):
   _constructor = ggplot2_env['stat_qq']
stat_qq = StatQQ.new

class StatQuantile(Stat):
   _constructor = ggplot2_env['stat_quantile']
stat_quantile = StatQuantile.new

class StatSmooth(Stat):
   _constructor = ggplot2_env['stat_smooth']
stat_smooth = StatSmooth.new

class StatSpoke(Stat):
   _constructor = ggplot2_env['stat_spoke']
stat_spoke = StatSpoke.new

class StatSum(Stat):
   _constructor = ggplot2_env['stat_sum']
stat_sum = StatSum.new

class StatSummary(Stat):
   _constructor = ggplot2_env['stat_summary']
stat_summary = StatSummary.new

class StatUnique(Stat):
   _constructor = ggplot2_env['stat_unique']
stat_unique = StatUnique.new

class StatVline(Stat):
   _constructor = ggplot2_env['stat_vline']
stat_vline = StatVline.new

class Coord(GBaseObject):
   pass

class CoordCartesian(Coord):
   _constructor = ggplot2_env['coord_cartesian']
coord_cartesian = CoordCartesian.new

class CoordEqual(Coord):
   _constructor = ggplot2_env['coord_equal']
coord_equal = CoordEqual.new

class CoordFlip(Coord):
   _constructor = ggplot2_env['coord_flip']
coord_flip = CoordFlip.new

class CoordMap(Coord):
   _constructor = ggplot2_env['coord_map']
coord_map = CoordMap.new

class CoordPolar(Coord):
   _constructor = ggplot2_env['coord_polar']
coord_polar = CoordPolar.new

class CoordTrans(Coord):
   _constructor = ggplot2_env['coord_trans']
coord_trans = CoordTrans.new


class Facet(GBaseObject):
   pass

class FacetGrid(Facet):
   _constructor = ggplot2_env['facet_grid']
facet_grid = FacetGrid.new

class FacetWrap(Facet):
   _constructor = ggplot2_env['facet_wrap']
facet_wrap = FacetWrap.new

class Geom(GBaseObject):
    pass

class GeomAbline(Geom):
   _constructor = ggplot2_env['geom_abline']
geom_abline = GeomAbline.new

class GeomArea(Geom):
   _constructor = ggplot2_env['geom_area']
geom_area = GeomArea.new

class GeomBar(Geom):
   _constructor = ggplot2_env['geom_bar']
geom_bar = GeomBar.new

class GeomBin2D(Geom):
   _constructor = ggplot2_env['geom_bin2d']
geom_bin2d = GeomBin2D.new

class GeomBlank(Geom):
   _constructor = ggplot2_env['geom_blank']
geom_blank = GeomBlank.new
   
class GeomBoxplot(Geom):
   _constructor = ggplot2_env['geom_boxplot']
geom_boxplot = GeomBoxplot.new
   
class GeomContour(Geom):
   _constructor = ggplot2_env['geom_contour']
geom_contour = GeomContour.new

class GeomCrossBar(Geom):
   _constructor = ggplot2_env['geom_crossbar']
geom_crossbar = GeomCrossBar.new

class GeomDensity(Geom):
   _constructor = ggplot2_env['geom_density']
geom_density = GeomDensity.new

class GeomDensity2D(Geom):
   _constructor = ggplot2_env['geom_density2d']
geom_density2d = GeomDensity2D.new

class GeomErrorBar(Geom):
   _constructor = ggplot2_env['geom_errorbar']
geom_errorbar = GeomErrorBar.new

class GeomErrorBarH(Geom):
   _constructor = ggplot2_env['geom_errorbarh']
geom_errorbarh = GeomErrorBarH.new

class GeomFreqPoly(Geom):
   _constructor = ggplot2_env['geom_freqpoly']
geom_freqpoly = GeomFreqPoly.new

class GeomHex(Geom):
   _constructor = ggplot2_env['geom_hex']
geom_hex = GeomHex.new

class GeomHistogram(Geom):
   _constructor = ggplot2_env['geom_histogram']
geom_histogram = GeomHistogram.new

class GeomHLine(Geom):
   _constructor = ggplot2_env['geom_hline']
geom_hline = GeomHLine.new

class GeomJitter(Geom):
   _constructor = ggplot2_env['geom_jitter']
geom_jitter = GeomJitter.new

class GeomLine(Geom):
   _constructor = ggplot2_env['geom_line']
geom_line = GeomLine.new

class GeomLineRange(Geom):
   _constructor = ggplot2_env['geom_linerange']
geom_linerange = GeomLineRange.new
   
class GeomPath(Geom):
   _constructor = ggplot2_env['geom_path']
geom_path = GeomPath.new

class GeomPoint(Geom):
   _constructor = ggplot2_env['geom_point']
geom_point = GeomPoint.new

class GeomPointRange(Geom):
   _constructor = ggplot2_env['geom_pointrange']
geom_pointrange = GeomPointRange.new

class GeomPolygon(Geom):
   _constructor = ggplot2_env['geom_polygon']
geom_polygon = GeomPolygon.new

class GeomQuantile(Geom):
   _constructor = ggplot2_env['geom_quantile']
geom_quantile = GeomQuantile.new

class GeomRect(Geom):
   _constructor = ggplot2_env['geom_rect']
geom_rect = GeomRect.new

class GeomRibbon(Geom):
   _constructor = ggplot2_env['geom_ribbon']
geom_ribbon = GeomRibbon.new

class GeomRug(Geom):
   _constructor = ggplot2_env['geom_rug']
geom_rug = GeomRug.new

class GeomSegment(Geom):
   _constructor = ggplot2_env['geom_segment']
geom_segment = GeomSegment.new

class GeomSmooth(Geom):
   _constructor = ggplot2_env['geom_smooth']
geom_smooth = GeomSmooth.new

class GeomStep(Geom):
   _constructor = ggplot2_env['geom_step']
geom_step = GeomStep.new

class GeomText(Geom):
   _constructor = ggplot2_env['geom_text']
geom_text = GeomText.new

class GeomTile(Geom):
   _constructor = ggplot2_env['geom_tile']
geom_tile = GeomTile.new

class GeomVLine(Geom):
   _constructor = ggplot2_env['geom_vline']
geom_vline = GeomVLine.new

class Position(GBaseObject):
   pass

class PositionDodge(Position):
   _constructor = ggplot2_env['position_dodge']
position_dodge = PositionDodge.new
class PositionFill(Position):
   _constructor = ggplot2_env['position_fill']
position_fill = PositionFill.new
class PositionIdentify(Position):
   _constructor = ggplot2_env['position_identity']
position_identity = PositionIdentify.new
class PositionJitter(Position):
   _constructor = ggplot2_env['position_jitter']
position_jitter = PositionJitter.new
class PositionStack(Position):
   _constructor = ggplot2_env['position_stack']
position_stack = PositionStack.new

class Scale(GBaseObject):
   pass

class ScaleAlpha(Scale):
   _constructor = ggplot2_env['scale_alpha']
scale_alpha = ScaleAlpha.new
class ScaleColour(Scale):
   _constructor = ggplot2_env['scale_colour']
scale_colour = ScaleColour.new
class ScaleDiscrete(Scale):
   _constructor = ggplot2_env['scale_discrete']
scale_discrete = ScaleDiscrete.new
class ScaleLinetype(Scale):
   _constructor = ggplot2_env['scale_linetype']
scale_linetype = ScaleLinetype.new
class ScaleShape(Scale):
   _constructor = ggplot2_env['scale_shape']
scale_shape = ScaleShape.new
class ScaleSize(Scale):
   _constructor = ggplot2_env['scale_size']
scale_size = ScaleSize.new

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

