"""
Wrapper for the popular R library ggplot2.

With rpy2, the most convenient general way to
import packages is to use `importr()`, for example
with ggplot2::

    from rpy2.robjects.packages import importr
    ggplot2 = importr('ggplot2')

This module is an supplementary layer in which an attempt
at modelling the package as it was really developed
as Python package is made. Behind the scene, `importr()`
is used and can be accessed with:

    from robjects.robjects.lib import ggplot2
    ggplot2.ggplot2

GGplot2 is designed using a prototype-based approach to
Object-Oriented Programming, and this module is trying
to define class-hierachies so the nature of a given
instance can be identified more easily.

The main families of classes are:

- GGplot
- Aes and AesString
- Layer
- Stat

A downside of the approach is that the code in the
module is 'hand-made'. In hindsight, this can be tedious
to maintain and document but this is a good showcase of
"manual" mapping of R code into Python classes.

The codebase in R for ggplot2 has evolved since this
was initially written, and many functions have
signature-defined parameters (used to be ellipsis
about everywhere). Metaprogramming will hopefully
be added to shorten the Python code in the module,
and provide a more dynamic mapping.

"""

import rpy2.robjects as robjects
import rpy2.robjects.constants
import rpy2.robjects.conversion as conversion
from rpy2.robjects.packages import importr, WeakPackage
from rpy2.robjects import rl
import warnings

NULL = robjects.NULL

rlang = importr('rlang', on_conflict='warn',
                robject_translations={'.env': '__env'})
lazyeval = importr('lazyeval', on_conflict='warn')
base = importr('base', on_conflict='warn')
ggplot2 = importr('ggplot2', on_conflict='warn')
ggplot2 = WeakPackage(ggplot2._env,
                      ggplot2.__rname__,
                      translation=ggplot2._translation,
                      exported_names=ggplot2._exported_names,
                      on_conflict="warn",
                      version=ggplot2.__version__,
                      symbol_r2python=ggplot2._symbol_r2python,
                      symbol_resolve=ggplot2._symbol_resolve)

TARGET_VERSION = '3.3.'
if not ggplot2.__version__.startswith(TARGET_VERSION):
    warnings.warn(
        'This was designed againt ggplot2 versions starting with %s but you '
        'have %s' % (TARGET_VERSION, ggplot2.__version__))
ggplot2_env = robjects.baseenv['as.environment']('package:ggplot2')

StrVector = robjects.StrVector


def as_symbol(x):
    return rlang.sym(x)


_AES_RLANG = rl('ggplot2::aes()')


class GGPlot(robjects.vectors.ListVector):
    """ A Grammar of Graphics Plot.

    GGPlot instances can be added to one an other in order to construct
    the final plot (the method `__add__()` is implemented).
    """

    _constructor = ggplot2._env['ggplot']
    _rprint = ggplot2._env['print.ggplot']
    _add = ggplot2._env['%+%']

    @classmethod
    def new(cls, data, mapping=_AES_RLANG, **kwargs):
        """ Constructor for the class GGplot. """
        data = conversion.py2rpy(data)
        res = cls(cls._constructor(data, mapping=mapping, **kwargs))
        return res

    def plot(self, vp=rpy2.robjects.constants.NULL):
        self._rprint(self, vp=vp)

    def __add__(self, obj):
        res = self._add(self, obj)
        if 'gg' not in res.rclass:
            raise ValueError(
                "Added object did not give a ggplot result "
                "(get class '%s')." % res.rclass[0])
        return self.__class__(res)

    def save(self, filename, **kwargs):
        """ Save the plot ( calls R's `ggplot2::ggsave()` ) """
        ggplot2.ggsave(filename=filename, plot=self, **kwargs)


ggplot = GGPlot.new


class Aes(robjects.ListVector):
    """ Aesthetics mapping, using expressions rather than string
    (this is the most common form when using the package in R - it might
    be easier to use AesString when working in Python using rpy2 -
    see class AesString in this Python module).
    """
    _constructor = ggplot2_env['aes']

    @classmethod
    def new(cls, *args, **kwargs):
        res = cls(cls._constructor(*args, **kwargs))
        return res


aes = Aes.new


class Vars(robjects.ListVector):
    """ Aesthetics mapping, using expressions rather than string
    (this is the most common form when using the package in R - it might
    be easier to use AesString when working in Python using rpy2 -
    see class AesString in this Python module).
    """
    _constructor = ggplot2_env['vars']

    @classmethod
    def new(cls, *args):
        """Constructor for the class Vars."""
        new_args = list()
        for a in args:
            new_args.append(
                rlang.parse_quo(
                    a, env=robjects.baseenv['sys.frame']()
                )
            )
        res = cls(cls._constructor(*new_args))
        return res


vars = Vars.new


class AesString(robjects.ListVector):
    """ Aesthetics mapping, using strings rather than expressions (the later
    being most common form when using the package in R - see class Aes
    in this Python module).

    This associates dimensions in the data sets (columns in the DataFrame),
    possibly with a transformation applied on-the-fly (e.g., "log(value)",
    or "cost / benefits") to graphical "dimensions" in a chosen graphical
    representation (e.g., x-axis, color of points, size, etc...).

    Not all graphical representations have all dimensions. Refer to the
    documentation of ggplot2, online tutorials, or Hadley's book for
    more details.
    """
    _constructor = ggplot2_env['aes_string']

    @classmethod
    def new(cls, **kwargs):
        """Constructor for the class AesString."""
        res = cls(cls._constructor(**kwargs))
        return res


aes_string = AesString.new


class Layer(robjects.RObject):
    """ At this level, aesthetics mapping can (should ?) be specified
     (see Aes and AesString). """
    _constructor = ggplot2_env['layer']

    @classmethod
    def new(cls,
            *args, **kwargs):
        """ Constructor for the class Layer. """
        for i, elt in enumerate(args):
            args[i] = conversion.py2ro(elt)

        for k in kwargs:
            kwargs[k] = conversion.py2ro(kwargs[k])

        res = cls(cls.contructor)(*args, **kwargs)
        return res


layer = Layer.new


class GBaseObject(robjects.Environment):
    @classmethod
    def new(cls, *args, **kwargs):
        args_list = list(args)
        res = cls(cls._constructor(*args_list, **kwargs))
        return res


class Stat(GBaseObject):
    """ A "statistical" processing of the data in order
    to make a plot, or a plot element.

    This is an abstract class; material classes are called
    Stat* (e.g., StatAbline, StatBin, etc...). """
    pass


class StatBin(Stat):
    """ Bin data. """
    _constructor = ggplot2_env['stat_bin']


stat_bin = StatBin.new


class StatBin2D(Stat):
    """ 2D binning of data into squares/rectangles. """
    _constructor = ggplot2_env['stat_bin_2d']


stat_bin2d = StatBin2D.new
stat_bin_2d = StatBin2D.new


class StatBinhex(Stat):
    """ 2D binning of data into hexagons. """
    _constructor = ggplot2_env['stat_bin_hex']


stat_binhex = StatBinhex.new
stat_bin_hex = StatBinhex.new


class StatBoxplot(Stat):
    """ Components of box and whisker plot. """
    _constructor = ggplot2_env['stat_boxplot']


stat_boxplot = StatBoxplot.new


class StatContour(Stat):
    """ Contours of 3D data. """
    _constructor = ggplot2_env['stat_contour']


stat_contour = StatContour.new


class StatDensity(Stat):
    """ 1D density estimate """
    _constructor = ggplot2_env['stat_density']


stat_density = StatDensity.new


class StatDensity2D(Stat):
    """ 2D density estimate """
    _constructor = ggplot2_env['stat_density_2d']


stat_density2d = StatDensity2D.new
stat_density_2d = StatDensity2D.new


class StatFunction(Stat):
    """ Superimpose a function """
    _constructor = ggplot2_env['stat_function']


stat_function = StatFunction.new


class StatIdentity(Stat):
    """ Identity function """
    _constructor = ggplot2_env['stat_identity']


stat_identity = StatIdentity.new


class StatQQ(Stat):
    """ Calculation for quantile-quantile plot. """
    _constructor = ggplot2_env['stat_qq']


stat_qq = StatQQ.new


class StatQuantile(Stat):
    """ Continuous quantiles """
    _constructor = ggplot2_env['stat_quantile']


stat_quantile = StatQuantile.new


class StatSmooth(Stat):
    """ Smoothing function """
    _constructor = ggplot2_env['stat_smooth']


stat_smooth = StatSmooth.new


class StatSpoke(Stat):
    """ Convert angle and radius to xend and yend """
    _constructor = ggplot2_env['stat_spoke']


stat_spoke = StatSpoke.new


class StatSum(Stat):
    """ Sum unique values.
    Useful when overplotting. """
    _constructor = ggplot2_env['stat_sum']


stat_sum = StatSum.new


class StatSummary(Stat):
    """ Summarize values for y at every unique value for x"""
    _constructor = ggplot2_env['stat_summary']


stat_summary = StatSummary.new


class StatSummary2D(Stat):
    """ Summarize values for y at every unique value for x"""
    _constructor = ggplot2_env['stat_summary_2d']


stat_summary2d = StatSummary2D.new
stat_summary_2d = StatSummary2D.new


class StatUnique(Stat):
    """ Remove duplicates. """
    _constructor = ggplot2_env['stat_unique']


stat_unique = StatUnique.new


class Coord(GBaseObject):
    """ Coordinates """
    pass


class CoordFixed(Coord):
    """ Cartesian coordinates with fixed relationship
    (that is fixed ratio between units in axes).
    CoordEquel seems to be identical to this class."""
    _constructor = ggplot2_env['coord_fixed']


coord_fixed = CoordFixed.new


class CoordCartesian(Coord):
    """ Cartesian coordinates. """
    _constructor = ggplot2_env['coord_cartesian']


coord_cartesian = CoordCartesian.new


class CoordEqual(Coord):
    """ This class seems to be identical to CoordFixed. """
    _constructor = ggplot2_env['coord_equal']


coord_equal = CoordEqual.new


class CoordFlip(Coord):
    """ Flip horizontal and vertical coordinates. """
    _constructor = ggplot2_env['coord_flip']


coord_flip = CoordFlip.new


class CoordMap(Coord):
    """ Map projections. """
    _constructor = ggplot2_env['coord_map']


coord_map = CoordMap.new


class CoordPolar(Coord):
    """ Polar coordinates. """
    _constructor = ggplot2_env['coord_polar']


coord_polar = CoordPolar.new


class CoordTrans(Coord):
    """ Apply transformations (functions) to a cartesian coordinate system. """
    _constructor = ggplot2_env['coord_trans']


coord_trans = CoordTrans.new


class Facet(GBaseObject):
    """ Panels """
    pass


class FacetGrid(Facet):
    """ Panels in a grid. """
    _constructor = ggplot2_env['facet_grid']


facet_grid = FacetGrid.new


class FacetWrap(Facet):
    """ Sequence of panels in a 2D layout """
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


class GeomCol(Geom):
    _constructor = ggplot2_env['geom_col']


geom_col = GeomCol.new


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
    _constructor = ggplot2_env['geom_density_2d']


geom_density2d = GeomDensity2D.new
geom_density_2d = GeomDensity2D.new


class GeomDotplot(Geom):
    _constructor = ggplot2_env['geom_dotplot']


geom_dotplot = GeomDotplot.new


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


class GeomRaster(Geom):
    _constructor = ggplot2_env['geom_raster']


geom_raster = GeomRaster.new


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


class GeomSpoke(Geom):
    """ Convert angle and radius to xend and yend """
    _constructor = ggplot2_env['geom_spoke']


geom_spoke = GeomSpoke.new


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


class ScaleRadius(Scale):
    _constructor = ggplot2_env['scale_radius']


scale_radius = ScaleRadius.new


class ScaleSize(Scale):
    _constructor = ggplot2_env['scale_size']


scale_size = ScaleSize.new


class ScaleSizeArea(Scale):
    _constructor = ggplot2_env['scale_size_area']


scale_size_area = ScaleSizeArea.new


class ScaleShapeDiscrete(Scale):
    _constructor = ggplot2_env['scale_shape_discrete']


scale_shape_discrete = ScaleShapeDiscrete.new


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
scale_color_brewer = scale_colour_brewer


class ScaleColourContinuous(ScaleColour):
    _constructor = ggplot2_env['scale_colour_continuous']


scale_colour_continuous = ScaleColourContinuous.new
scale_color_continuous = scale_colour_continuous


class ScaleColourDiscrete(ScaleColour):
    _constructor = ggplot2_env['scale_colour_discrete']


scale_colour_discrete = ScaleColourDiscrete.new
scale_color_discrete = scale_colour_discrete


class ScaleColourGradient(ScaleColour):
    _constructor = ggplot2_env['scale_colour_gradient']


scale_colour_gradient = ScaleColourGradient.new
scale_color_gradient = scale_colour_gradient


class ScaleColourGradient2(ScaleColour):
    _constructor = ggplot2_env['scale_colour_gradient2']


scale_colour_gradient2 = ScaleColourGradient2.new
scale_color_gradient2 = scale_colour_gradient2


class ScaleColourGradientN(ScaleColour):
    _constructor = ggplot2_env['scale_colour_gradientn']


scale_colour_gradientn = ScaleColourGradientN.new
scale_color_gradientn = scale_colour_gradientn


class ScaleColourGrey(ScaleColour):
    _constructor = ggplot2_env['scale_colour_grey']


scale_colour_grey = ScaleColourGrey.new
scale_color_grey = scale_colour_grey


class ScaleColourHue(ScaleColour):
    _constructor = ggplot2_env['scale_colour_hue']


scale_colour_hue = ScaleColourHue.new
scale_color_hue = scale_colour_hue


class ScaleColourIdentity(ScaleColour):
    _constructor = ggplot2_env['scale_colour_identity']


scale_colour_identity = ScaleColourIdentity.new
scale_color_identity = scale_colour_identity


class ScaleColourManual(ScaleColour):
    _constructor = ggplot2_env['scale_colour_manual']


scale_colour_manual = ScaleColourManual.new
scale_color_manual = scale_colour_manual


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


class ScaleLinetypeContinuous(ScaleLinetype):
    _constructor = ggplot2_env['scale_linetype_continuous']


scale_linetype_continuous = ScaleLinetypeContinuous.new


class ScaleLinetypeDiscrete(ScaleLinetype):
    _constructor = ggplot2_env['scale_linetype_discrete']


scale_linetype_discrete = ScaleLinetypeDiscrete.new


class ScaleLinetypeManual(ScaleLinetype):
    _constructor = ggplot2_env['scale_linetype_manual']


scale_linetype_manual = ScaleLinetypeManual.new


class ScaleShapeManual(ScaleShape):
    _constructor = ggplot2_env['scale_shape_manual']


scale_shape_manual = ScaleShapeManual.new


guides = ggplot2.guides
guide_colorbar = ggplot2.guide_colorbar
guide_colourbar = ggplot2.guide_colourbar
guide_legend = ggplot2.guide_legend


class Options(robjects.ListVector):

    def __repr__(self):
        s = '<instance of %s : %i>' % (type(self), id(self))
        return s


class Element(Options):
    pass


class ElementText(Element):

    _constructor = ggplot2.element_text

    @classmethod
    def new(cls, family='', face='plain', colour='black', size=10,
            hjust=0.5, vjust=0.5, angle=0, lineheight=1.1,
            color=NULL):
        res = cls(cls._constructor(family=family, face=face,
                                   colour=colour, size=size,
                                   hjust=hjust, vjust=vjust,
                                   angle=angle, lineheight=lineheight))
        return res


element_text = ElementText.new


class ElementRect(Element):

    _constructor = ggplot2.element_rect

    @classmethod
    def new(cls, fill=NULL, colour=NULL, size=NULL,
            linetype=NULL, color=NULL):
        res = cls(cls._constructor(fill=fill, colour=colour,
                                   size=size, linetype=linetype,
                                   color=color))
        return res


element_rect = ElementRect.new


class Labs(Options):
    _constructor = ggplot2.labs

    @classmethod
    def new(cls, **kwargs):
        res = cls(cls._constructor(**kwargs))
        return res


labs = Labs.new


class Theme(Options):
    pass


class ElementBlank(Theme):
    _constructor = ggplot2.element_blank

    @classmethod
    def new(cls):
        res = cls(cls._constructor())
        return res


element_blank = ElementBlank.new


theme_get = ggplot2.theme_get


class ThemeGrey(Theme):
    _constructor = ggplot2.theme_grey

    @classmethod
    def new(cls, base_size=12):
        res = cls(cls._constructor(base_size=base_size))
        return res


theme_grey = ThemeGrey.new


class ThemeClassic(Theme):
    _constructor = ggplot2.theme_classic

    @classmethod
    def new(cls, base_size=12, base_family=''):
        res = cls(cls._constructor(base_size=base_size,
                                   base_family=base_family))
        return res


theme_classic = ThemeClassic.new


class ThemeDark(Theme):
    _constructor = ggplot2.theme_dark

    @classmethod
    def new(cls, base_size=12, base_family=''):
        res = cls(cls._constructor(base_size=base_size,
                                   base_family=base_family))
        return res


theme_dark = ThemeDark.new


class ThemeLight(Theme):
    _constructor = ggplot2.theme_light

    @classmethod
    def new(cls, base_size=12, base_family=''):
        res = cls(cls._constructor(base_size=base_size,
                                   base_family=base_family))
        return res


theme_light = ThemeLight.new


class ThemeBW(Theme):
    _constructor = ggplot2.theme_bw

    @classmethod
    def new(cls, base_size=12):
        res = cls(cls._constructor(base_size=base_size))
        return res


theme_bw = ThemeBW.new


class ThemeGray(Theme):
    _constructor = ggplot2.theme_gray

    @classmethod
    def new(cls, base_size=12):
        res = cls(cls._constructor(base_size=base_size))
        return res


theme_gray = ThemeGray.new
theme_grey = theme_gray


class ThemeMinimal(Theme):
    _constructor = ggplot2.theme_minimal

    @classmethod
    def new(cls, base_size=12, base_family=''):
        res = cls(cls._constructor(base_size=base_size,
                                   base_family=base_family))
        return res


theme_minimal = ThemeMinimal.new


class ThemeLinedraw(Theme):
    _constructor = ggplot2.theme_linedraw

    @classmethod
    def new(cls, base_size=12, base_family=""):
        res = cls(cls._constructor(base_size=base_size,
                                   base_family=base_family))
        return res


theme_linedraw = ThemeLinedraw.new


class ThemeVoid(Theme):
    _constructor = ggplot2.theme_void

    @classmethod
    def new(cls, base_size=12, base_family=''):
        res = cls(cls._constructor(base_size=base_size,
                                   base_family=base_family))
        return res


theme_void = ThemeVoid.new


theme_set = ggplot2.theme_set

theme_update = ggplot2.theme_update

gplot = ggplot2.qplot

map_data = ggplot2.map_data

theme = ggplot2_env['theme']

ggtitle = ggplot2.ggtitle
xlab = ggplot2.xlab
ylab = ggplot2.ylab
guide_axis = ggplot2.guide_axis
guide_bins = ggplot2.guide_bins
guide_colorbar = ggplot2.guide_colorbar
guide_colourbar = guide_colorbar
guide_colorsteps = ggplot2.guide_colorsteps
guide_coloursteps = guide_colorsteps
guide_geom = ggplot2.guide_geom
guide_legend = ggplot2.guide_legend
guide_merge = ggplot2.guide_merge
guide_none = ggplot2.guide_none
guide_train = ggplot2.guide_train
guide_transform = ggplot2.guide_transform


def dict2rvec(d):
    """Convert a python dict[str, str] into an R named vector.
    """
    r_x = StrVector(list(d.values()))
    r_x.names = list(d.keys())
    return r_x


as_labeller = ggplot2.as_labeller

original_rpy2py = conversion.rpy2py


def ggplot2_conversion(robj):

    pyobj = original_rpy2py(robj)

    try:
        rcls = pyobj.rclass
    except AttributeError:
        # conversion lead to something that is no
        # longer an R object
        return pyobj

    if (rcls is not None) and (rcls[0] == 'gg'):
        pyobj = GGPlot(pyobj)

    return pyobj


conversion.rpy2py = ggplot2_conversion
