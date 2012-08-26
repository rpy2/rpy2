import rpy2.robjects.methods
import rpy2.robjects as robjects
import rpy2.robjects.conversion as conversion
import rpy2.rinterface as rinterface
from rpy2.robjects.packages import importr
import copy

NULL = robjects.NULL

#getmethod = robjects.baseenv.get("getMethod")

rimport = robjects.baseenv.get('library')
ggplot2 = importr('ggplot2')

ggplot2_env = robjects.baseenv['as.environment']('package:ggplot2')

StrVector = robjects.StrVector

def as_symbol(x):
   res = rinterface.parse(x)
   return res

class GGPlot(robjects.RObject):

    _constructor = ggplot2._env['ggplot']
    _rprint = ggplot2._env['print.ggplot']
    _add = ggplot2._env['+.ggplot']

    @classmethod
    def new(cls, data):
        res = cls(cls._constructor(data))
        return res
    
    def plot(self, vp = robjects.constants.NULL):
        self._rprint(self, vp = vp)

    def __add__(self, obj):
        res = self._add(self, obj)
        if res.rclass[0] != 'ggplot':
           raise ValueError("Added object did not give a ggplot result (get class '%s')." % res.rclass[0])
        return GGPlot(res)

ggplot = GGPlot.new


class Aes(robjects.Vector):
    _constructor = ggplot2_env['aes']
    
    @classmethod
    def new(cls, **kwargs):
       new_kwargs = copy.copy(kwargs)
       for k,v in kwargs.iteritems():
          new_kwargs[k] = as_symbol(v)
       res = cls(cls._constructor(**new_kwargs))
       return res
aes = Aes.new

class AesString(robjects.Vector):
    _constructor = ggplot2_env['aes_string']
    
    @classmethod
    def new(cls, **kwargs):
       new_kwargs = copy.copy(kwargs)
       for k,v in kwargs.iteritems():
          new_kwargs[k] = as_symbol(v)
       res = cls(cls._constructor(**new_kwargs))
       return res
aes_string = AesString.new


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
   pass
class ScaleDiscrete(Scale):
   pass
class ScaleLinetype(Scale):
   _constructor = ggplot2_env['scale_linetype']
scale_linetype = ScaleLinetype.new
class ScaleShape(Scale):
   _constructor = ggplot2_env['scale_shape']
scale_shape = ScaleShape.new
class ScaleSize(Scale):
   _constructor = ggplot2_env['scale_size']
scale_size = ScaleSize.new

class ScaleFill(Scale):
   pass
class ScaleX(Scale):
   pass
class ScaleY(Scale):
   pass

# class Limits(Scale):
#    _constructor = ggplot2_env['limits']
# limits = Limits.new

class XLim(Scale):
   _constructor = ggplot2_env['xlim']
xlim = XLim.new

class YLim(Scale):
   _constructor = ggplot2_env['ylim']
ylim = YLim.new


class ScaleXContinuous(ScaleX):
   _constructor = ggplot2_env['scale_x_continuous']
scale_x_continuous = ScaleXContinuous.new
class ScaleYContinuous(ScaleY):
   _constructor = ggplot2_env['scale_y_continuous']
scale_y_continuous = ScaleYContinuous.new
class ScaleXDiscrete(ScaleX):
   _constructor = ggplot2_env['scale_x_discrete']
scale_x_discrete = ScaleXDiscrete.new
class ScaleYDiscrete(ScaleY):
   _constructor = ggplot2_env['scale_y_discrete']
scale_y_discrete = ScaleYDiscrete.new
class ScaleXDate(ScaleX):
   _constructor = ggplot2_env['scale_x_date']
scale_x_date = ScaleXDate.new
class ScaleYDate(ScaleY):
   _constructor = ggplot2_env['scale_y_date']
scale_y_date = ScaleYDate.new
class ScaleXDatetime(ScaleX):
   _constructor = ggplot2_env['scale_x_datetime']
scale_x_datetime = ScaleXDatetime.new
class ScaleYDatetime(ScaleY):
   _constructor = ggplot2_env['scale_y_datetime']
scale_y_datetime = ScaleYDatetime.new
class ScaleXLog10(ScaleX):
   _constructor = ggplot2_env['scale_x_log10']
scale_x_log10 = ScaleXLog10.new
class ScaleYLog10(ScaleY):
   _constructor = ggplot2_env['scale_y_log10']
scale_y_log10 = ScaleYLog10.new
class ScaleXReverse(ScaleX):
   _constructor = ggplot2_env['scale_x_reverse']
scale_x_reverse = ScaleXReverse.new
class ScaleYReverse(ScaleY):
   _constructor = ggplot2_env['scale_y_reverse']
scale_y_reverse = ScaleYReverse.new
class ScaleXSqrt(ScaleX):
   _constructor = ggplot2_env['scale_x_sqrt']
scale_x_sqrt = ScaleXSqrt.new
class ScaleYSqrt(ScaleY):
   _constructor = ggplot2_env['scale_y_sqrt']
scale_y_sqrt = ScaleYSqrt.new
class ScaleColourBrewer(ScaleColour):
   _constructor = ggplot2_env['scale_colour_brewer']
scale_colour_brewer = ScaleColourBrewer.new
class ScaleColourContinuous(ScaleColour):
   _constructor = ggplot2_env['scale_colour_continuous']
scale_colour_continuous = ScaleColourContinuous.new
class ScaleColourDiscrete(ScaleColour):
   _constructor = ggplot2_env['scale_colour_discrete']
scale_colour_discrete = ScaleColourDiscrete.new
class ScaleColourGradient(ScaleColour):
   _constructor = ggplot2_env['scale_colour_gradient']
scale_colour_gradient = ScaleColourGradient.new
class ScaleColourGradient2(ScaleColour):
   _constructor = ggplot2_env['scale_colour_gradient2']
scale_colour_gradient2 = ScaleColourGradient2.new
class ScaleColourGradientN(ScaleColour):
   _constructor = ggplot2_env['scale_colour_gradientn']
scale_colour_gradientn = ScaleColourGradientN.new
class ScaleColourGrey(ScaleColour):
   _constructor = ggplot2_env['scale_colour_grey']
scale_colour_grey = ScaleColourGrey.new
class ScaleColourHue(ScaleColour):
   _constructor = ggplot2_env['scale_colour_hue']
scale_colour_hue = ScaleColourHue.new
class ScaleColourIdentity(ScaleColour):
   _constructor = ggplot2_env['scale_colour_identity']
scale_colour_identity = ScaleColourIdentity.new
class ScaleColourManual(ScaleColour):
   _constructor = ggplot2_env['scale_colour_manual']
scale_colour_manual = ScaleColourManual.new
class ScaleFillBrewer(ScaleFill):
   _constructor = ggplot2_env['scale_fill_brewer']
scale_fill_brewer = ScaleFillBrewer.new
class ScaleFillContinuous(ScaleFill):
   _constructor = ggplot2_env['scale_fill_continuous']
scale_fill_continuous = ScaleFillContinuous.new
class ScaleFillDiscrete(ScaleFill):
   _constructor = ggplot2_env['scale_fill_discrete']
scale_fill_discrete = ScaleFillDiscrete.new
class ScaleFillGradient(ScaleFill):
   _constructor = ggplot2_env['scale_fill_gradient']
scale_fill_gradient = ScaleFillGradient.new
class ScaleFillGradient2(ScaleFill):
   _constructor = ggplot2_env['scale_fill_gradient2']
scale_fill_gradient2 = ScaleFillGradient2.new
class ScaleFillGradientN(ScaleFill):
   _constructor = ggplot2_env['scale_fill_gradientn']
scale_fill_gradientn = ScaleFillGradientN.new
class ScaleFillGrey(ScaleFill):
   _constructor = ggplot2_env['scale_fill_grey']
scale_fill_grey = ScaleFillGrey.new
class ScaleFillHue(ScaleFill):
   _constructor = ggplot2_env['scale_fill_hue']
scale_fill_hue = ScaleFillHue.new
class ScaleFillIdentity(ScaleFill):
   _constructor = ggplot2_env['scale_fill_identity']
scale_fill_identity = ScaleFillIdentity.new
class ScaleFillManual(ScaleFill):
   _constructor = ggplot2_env['scale_fill_manual']
scale_fill_manual = ScaleFillManual.new
class ScaleLinetypeManual(ScaleLinetype):
   _constructor = ggplot2_env['scale_linetype_manual']
scale_linetype_manual = ScaleLinetypeManual.new
class ScaleShapeManual(ScaleShape):
   _constructor = ggplot2_env['scale_shape_manual']
scale_shape_manual = ScaleShapeManual.new


class Options(robjects.Vector):
   def __init__(self, obj):
      self.__sexp__ = obj.__sexp__

   def __repr__(self):
      s = '<instance of %s : %i>' %(type(self), id(self)) 
      return s

class Theme(Options):
   pass

class ThemeBlank(Theme):
    _constructor = ggplot2.theme_blank
    @classmethod
    def new(cls):
        res = cls(cls._constructor())
        return res

theme_blank = ThemeBlank.new

theme_get = ggplot2.theme_get

class ThemeGrey(Theme):
    _constructor = ggplot2.theme_grey
    @classmethod
    def new(cls, base_size = 12):
       res = cls(cls._constructor(base_size = base_size))
       return res

theme_grey = ThemeGrey.new

class ThemeRect(Theme):
    _constructor = ggplot2.theme_rect
    @classmethod
    def new(cls, fill = robjects.NA_Logical, colour = "black", 
            size = 0.5, linetype = 1):
       res = cls(cls._constructor(fill = fill, colour = colour, 
                                  size = size, linetype = linetype))
       return res
theme_rect = ThemeRect.new

class ThemeSegment(Theme):
    _constructor = ggplot2.theme_rect
    @classmethod
    def new(cls, colour = 'black', size = 0.5, linetype = 1):
       res = cls(cls._constructor(colour = colour, size = size,
                                  linetype = linetype))
       return res
theme_segment = ThemeSegment.new

# Theme text is not a vector :/
class ThemeText(robjects.Function):
    _constructor = ggplot2.theme_text
    @classmethod
    def new(cls, family = "", face = "plain", colour = "black", size = 10,
            hjust = 0.5, vjust = 0.5, angle = 0, lineheight = 1.1):
       res = cls(cls._constructor(family = family, face = face, 
                                  colour = colour, size = size,
                                  hjust = hjust, vjust = vjust, 
                                  angle = angle, lineheight = lineheight))
       return res
theme_text = ThemeText.new

class ThemeBW(Theme):
    _constructor = ggplot2.theme_bw
    @classmethod
    def new(cls, base_size = 12):
       res = cls(cls._constructor(base_size = base_size))
       return res

theme_bw = ThemeBW.new

class ThemeGray(Theme):
    _constructor = ggplot2.theme_gray
    @classmethod
    def new(cls, base_size = 12):
       res = cls(cls._constructor(base_size = base_size))
       return res
theme_gray = ThemeGray.new

class ThemeLine(Theme):
    _constructor = ggplot2.theme_line
    @classmethod
    def new(cls, colour = 'black', size = 0.5, linetype = 1):
       res = cls(cls._constructor(colour = colour, size = size,
                                  linetype = linetype))
       return res
theme_line = ThemeLine.new

#theme_render
theme_set = ggplot2.theme_set

theme_update = ggplot2.theme_update  

gplot = ggplot2.qplot

map_data = ggplot2.map_data

opts = ggplot2_env['opts']


original_conversion = conversion.ri2py
def ggplot2_conversion(robj):

    pyobj = original_conversion(robj)

    rcls = pyobj.rclass
    if rcls is NULL:
       rcls = (None, )

    if 'ggplot' in rcls:
       pyobj = GGPlot(pyobj)

    return pyobj

conversion.ri2py = ggplot2_conversion

