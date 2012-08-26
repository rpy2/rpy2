
#-- setup-begin
from rpy2 import robjects
from rpy2.robjects import Formula
from rpy2.robjects.vectors import IntVector, FloatVector
from rpy2.robjects.lib import grid
from rpy2.robjects.packages import importr

# The R 'print' function
rprint = robjects.globalenv.get("print")
stats = importr('stats')
grdevices = importr('grDevices')
base = importr('base')
#-- setup-end

#-- setuplattice-begin
lattice = importr('lattice')
#-- setuplattice-end
#-- setupxyplot-begin
xyplot = lattice.xyplot
#-- setupxyplot-end

#-- dataset-begin
rnorm = stats.rnorm
dataf_rnorm = robjects.DataFrame({'value': rnorm(300, mean=0) + rnorm(100, mean=3),
                                  'other_value': rnorm(300, mean=0) + rnorm(100, mean=3),
                                  'mean': IntVector([0, ]*300 + [3, ] * 100)})
#-- dataset-end

grdevices.png('../../_static/graphics_lattice_xyplot_1.png',
              width = 612, height = 612, antialias="subpixel", type="cairo")
#-- xyplot1-begin
utils = importr('utils')
tmpenv = robjects.Environment()
utils.data("mtcars", package = "datasets", envir = tmpenv)
mtcars = tmpenv["mtcars"]
formula = Formula('mpg ~ wt')
formula.getenvironment()['mpg'] = mtcars.rx2('mpg')
formula.getenvironment()['wt'] = mtcars.rx2('wt')

p = lattice.xyplot(formula)
rprint(p)
#-- xyplot1-end
grdevices.dev_off()

grdevices.png('../../_static/graphics_lattice_xyplot_2.png',
    width = 612, height = 612, antialias="subpixel", type="cairo")
#-- xyplot2-begin
p = lattice.xyplot(formula, groups = mtcars.rx2('cyl'))
rprint(p)
#-- xyplot2-end
grdevices.dev_off()

grdevices.png('../../_static/graphics_lattice_xyplot_3.png',
    width = 912, height = 512, antialias="subpixel", type="cairo")
#-- xyplot3-begin
formula = Formula('mpg ~ wt | cyl')
formula.getenvironment()['mpg'] = mtcars.rx2('mpg')
formula.getenvironment()['wt'] = mtcars.rx2('wt')
formula.getenvironment()['cyl'] = mtcars.rx2('cyl')

p = lattice.xyplot(formula, layout = IntVector((3, 1)))
rprint(p)
#-- xyplot3-end
grdevices.dev_off()

grdevices.png('../../_static/graphics_lattice_bwplot_1.png',
    width = 912, height = 512, antialias="subpixel", type="cairo")
#-- bwplot1-begin
p = lattice.bwplot(Formula('mpg ~ factor(cyl) | gear'),
                   data = mtcars, fill = 'grey')
rprint(p, nrow=1)
#-- bwplot1-end
grdevices.dev_off()



grdevices.png('../../_static/graphics_lattice_wireframe_1.png',
    width = 612, height = 612, antialias="subpixel", type="cairo")
#-- wireframe1-begin
utils.data("volcano", package = "datasets", envir = tmpenv)
volcano = tmpenv["volcano"]

p = lattice.wireframe(volcano, shade = True,
                      zlab = "",
                      aspect = FloatVector((61.0/87, 0.4)),
                      light_source = IntVector((10,0,10)))
rprint(p)
#-- wireframe1-end
grdevices.dev_off()

grdevices.png('../../_static/graphics_lattice_wireframe_2.png',
    width = 912, height = 612, antialias="subpixel", type="cairo")
#-- wireframe2-begin
reshape2 = importr('reshape2')
dataf = reshape2.melt(volcano)
dataf = dataf.cbind(ct = lattice.equal_count(dataf.rx2("value"), number=3, overlap=1/4))
p = lattice.wireframe(Formula('value ~ Var1 * Var2 | ct'), 
                      data = dataf, shade = True,
                      aspect = FloatVector((61.0/87, 0.4)),
                      light_source = IntVector((10,0,10)))
rprint(p, nrow = 1)
#-- wireframe2-end
grdevices.dev_off()




#-- setupggplot2-begin
import math, datetime
import rpy2.robjects.lib.ggplot2 as ggplot2
import rpy2.robjects as ro
from rpy2.robjects.packages import importr
base = importr('base')

utils.data("mtcars", package = "datasets", envir = tmpenv)
mtcars = tmpenv["mtcars"]

#-- setupggplot2-end

grdevices.png('../../_static/graphics_ggplot2mtcars.png',
              width = 612, height = 612, antialias="subpixel", type="cairo")
#-- ggplot2mtcars-begin
gp = ggplot2.ggplot(mtcars)

pp = gp + \
     ggplot2.aes_string(x='wt', y='mpg') + \
     ggplot2.geom_point()

pp.plot()
#-- ggplot2mtcars-end
grdevices.dev_off()

grdevices.png('../../_static/graphics_ggplot2geombin2d.png',
              width = 1000, height = 350, antialias="subpixel", type="cairo")
grid.newpage()
grid.viewport(layout=grid.layout(1, 3)).push()

vp = grid.viewport(**{'layout.pos.col':1, 'layout.pos.row': 1})
#-- ggplot2geombin2d-begin
gp = ggplot2.ggplot(dataf_rnorm)

pp = gp + \
     ggplot2.aes_string(x='value', y='other_value') + \
     ggplot2.geom_bin2d() + \
     ggplot2.opts(title =  'geom_bin2d')
pp.plot(vp = vp)
#-- ggplot2geombin2d-end

vp = grid.viewport(**{'layout.pos.col':2, 'layout.pos.row': 1})
#-- ggplot2geomdensity2d-begin
gp = ggplot2.ggplot(dataf_rnorm)

pp = gp + \
     ggplot2.aes_string(x='value', y='other_value') + \
     ggplot2.geom_density2d() + \
     ggplot2.opts(title =  'geom_density2d')
pp.plot(vp = vp)
#-- ggplot2geomdensity2d-end

vp = grid.viewport(**{'layout.pos.col':3, 'layout.pos.row': 1})
#-- ggplot2geomhexbin-begin
gp = ggplot2.ggplot(dataf_rnorm)

pp = gp + \
     ggplot2.aes_string(x='value', y='other_value') + \
     ggplot2.geom_hex() + \
     ggplot2.opts(title =  'geom_hex')
pp.plot(vp = vp)
#-- ggplot2geomhexbin-end

grdevices.dev_off()




grdevices.png('../../_static/graphics_ggplot2geomboxplot.png',
              width = 612, height = 612, antialias="subpixel", type="cairo")
#-- ggplot2geomboxplot-begin
gp = ggplot2.ggplot(mtcars)

pp = gp + \
     ggplot2.aes_string(x='factor(cyl)', y='mpg') + \
     ggplot2.geom_boxplot()

pp.plot()
#-- ggplot2geomboxplot-end
grdevices.dev_off()


#-- ggplot2geomhistogram-begin
gp = ggplot2.ggplot(mtcars)

pp = gp + \
     ggplot2.aes_string(x='wt') + \
     ggplot2.geom_histogram()

#pp.plot()
#-- ggplot2geomhistogram-end

grdevices.png('../../_static/graphics_ggplot2geomhistogram.png',
              width = 900, height = 412, antialias="subpixel", type="cairo")
grid.newpage()
grid.viewport(layout=grid.layout(1, 3)).push()

params = (('black', 'black'),
          ('black', 'white'),
          ('white', 'black'))
          
for col_i in range(3):
   vp = grid.viewport(**{'layout.pos.col':col_i+1, 'layout.pos.row': 1})
   outline_color, fill_color= params[col_i]
   pp = gp + \
        ggplot2.aes_string(x='wt') + \
        ggplot2.geom_histogram(col=outline_color, fill=fill_color) + \
        ggplot2.opts(title =  'col=%s - fill=%s' %params[col_i])
   pp.plot(vp = vp)
grdevices.dev_off()


grdevices.png('../../_static/graphics_ggplot2geomhistogramfillcyl.png',
              width = 612, height = 612, antialias="subpixel", type="cairo")
#-- ggplot2geomhistogramfillcyl-begin
gp = ggplot2.ggplot(mtcars)

pp = gp + \
     ggplot2.aes_string(x='wt', fill='factor(cyl)') + \
     ggplot2.geom_histogram()

pp.plot()
#-- ggplot2geomhistogramfillcyl-end
grdevices.dev_off()


grdevices.png('../../_static/graphics_ggplot2geompointdensity2d.png',
              width = 612, height = 612, antialias="subpixel", type="cairo")
#-- ggplot2geompointdensity2d-begin
gp = ggplot2.ggplot(dataf_rnorm)

pp = gp + \
     ggplot2.aes_string(x='value', y='other_value') + \
     ggplot2.geom_point(alpha = 0.3) + \
     ggplot2.geom_density2d(ggplot2.aes_string(col = '..level..')) + \
     ggplot2.opts(title =  'point + density')
pp.plot()
#-- ggplot2geompointdensity2d-end
grdevices.dev_off()


grdevices.png('../../_static/graphics_ggplot2geomfreqpolyfillcyl.png',
              width = 812, height = 412, antialias="subpixel", type="cairo")
grid.newpage()
grid.viewport(layout=grid.layout(1, 2)).push()

gp = ggplot2.ggplot(dataf_rnorm)

vp = grid.viewport(**{'layout.pos.col':1, 'layout.pos.row': 1})
pp = gp + \
     ggplot2.aes_string(x='value', col='factor(mean)') + \
     ggplot2.geom_freqpoly()
pp.plot(vp = vp)

vp = grid.viewport(**{'layout.pos.col':2, 'layout.pos.row': 1})
#-- ggplot2geomfreqpolyfillcyl-begin
pp = gp + \
     ggplot2.aes_string(x='value', fill='factor(mean)') + \
     ggplot2.geom_density(alpha = 0.5)
#-- ggplot2geomfreqpolyfillcyl-end
pp.plot(vp = vp)

grdevices.dev_off()



grdevices.png('../../_static/graphics_ggplot2geompointandrug.png',
              width = 612, height = 612, antialias="subpixel", type="cairo")
#-- ggplot2geompointandrug-begin
gp = ggplot2.ggplot(mtcars)

pp = gp + \
     ggplot2.aes_string(x='wt', y='mpg') + \
     ggplot2.geom_point() + \
     ggplot2.geom_rug()

pp.plot()
#-- ggplot2geompointandrug-end
grdevices.dev_off()



grdevices.png('../../_static/graphics_ggplot2mtcarscolcyl.png',
              width = 612, height = 612, antialias="subpixel", type="cairo")
#-- ggplot2mtcarscolcyl-begin
gp = ggplot2.ggplot(mtcars)

pp = gp + \
     ggplot2.aes_string(x='wt', y='mpg', col='factor(cyl)') + \
     ggplot2.geom_point()

pp.plot()
#-- ggplot2mtcarscolcyl-end
grdevices.dev_off()


grdevices.png('../../_static/graphics_ggplot2_ggplot_1.png',
              width = 612, height = 612, antialias="subpixel", type="cairo")
#-- ggplot1-begin
pp = gp + \
     ggplot2.aes_string(x='wt', y='mpg') + \
     ggplot2.geom_point() + \
     ggplot2.facet_grid(ro.Formula('. ~ cyl'))


pp.plot()
#-- ggplot1-end
grdevices.dev_off()



grdevices.png('../../_static/graphics_ggplot2aescolsize.png',
              width = 612, height = 612, antialias="subpixel", type="cairo")
#-- ggplot2aescolsize-begin
pp = gp + \
     ggplot2.aes_string(x='wt', y='mpg', size='factor(carb)',
                 col='factor(cyl)', shape='factor(gear)') + \
     ggplot2.geom_point()

pp.plot()
#-- ggplot2aescolsize-end
grdevices.dev_off()

grdevices.png('../../_static/graphics_ggplot2aescolboxplot.png',
              width = 612, height = 612, antialias="subpixel", type="cairo")
#-- ggplot2aescolboxplot-begin
gp = ggplot2.ggplot(mtcars)

pp = gp + \
     ggplot2.aes_string(x='factor(cyl)', y='mpg', fill='factor(cyl)') + \
     ggplot2.geom_boxplot()

pp.plot()
#-- ggplot2aescolboxplot-end
grdevices.dev_off()




grdevices.png('../../_static/graphics_ggplot2_qplot_4.png',
              width = 612, height = 612, antialias="subpixel", type="cairo")
#-- qplot4-begin
pp = gp + \
     ggplot2.aes_string(x='wt', y='mpg') + \
     ggplot2.geom_point() + \
     ggplot2.geom_abline(intercept = 30)
pp.plot()
#-- qplot4-end
grdevices.dev_off()

grdevices.png('../../_static/graphics_ggplot2_qplot_5.png',
              width = 612, height = 612, antialias="subpixel", type="cairo")
#-- qplot3addline-begin
pp = gp + \
     ggplot2.aes_string(x='wt', y='mpg') + \
     ggplot2.geom_point() + \
     ggplot2.geom_abline(intercept = 30) + \
     ggplot2.geom_abline(intercept = 15)
pp.plot()
#-- qplot3addline-end
grdevices.dev_off()


grdevices.png('../../_static/graphics_ggplot2addsmooth.png',
              width = 612, height = 612, antialias="subpixel", type="cairo")
#-- ggplot2addsmooth-begin
pp = gp + \
     ggplot2.aes_string(x='wt', y='mpg') + \
     ggplot2.geom_point() + \
     ggplot2.stat_smooth(method = 'lm')
pp.plot()

#-- ggplot2addsmooth-end
grdevices.dev_off()


grdevices.png('../../_static/graphics_ggplot2addsmoothmethods.png',
              width = 1024, height = 340, antialias="subpixel", type="cairo")

#-- ggplot2addsmoothmethods-begin
grid.newpage()
grid.viewport(layout=grid.layout(1, 3)).push()

params = (('lm', 'y ~ x'),
          ('lm', 'y ~ poly(x, 2)'),
          ('loess', 'y ~ x'))
          
for col_i in (1,2,3):
   vp = grid.viewport(**{'layout.pos.col':col_i, 'layout.pos.row': 1})
   method, formula = params[col_i-1]
   gp = ggplot2.ggplot(mtcars)
   pp = gp + \
        ggplot2.aes_string(x='wt', y='mpg') + \
        ggplot2.geom_point() + \
        ggplot2.stat_smooth(method = method, formula=formula) + \
        ggplot2.opts(title = method + ' - ' + formula)
   pp.plot(vp = vp)

#-- ggplot2addsmoothmethods-end
grdevices.dev_off()



grdevices.png('../../_static/graphics_ggplot2smoothblue.png',
              width = 612, height = 612, antialias="subpixel", type="cairo")
#-- ggplot2smoothblue-begin
pp = gp + \
     ggplot2.aes_string(x='wt', y='mpg') + \
     ggplot2.geom_point() + \
     ggplot2.stat_smooth(method = 'lm', fill = 'blue',
                         color = 'red', size = 3)
pp.plot()
#-- ggplot2smoothblue-end
grdevices.dev_off()

grdevices.png('../../_static/graphics_ggplot2smoothbycyl.png',
              width = 612, height = 612, antialias="subpixel", type="cairo")
#-- ggplot2smoothbycyl-begin
pp = gp + \
     ggplot2.aes_string(x='wt', y='mpg') + \
     ggplot2.geom_point() + \
     ggplot2.geom_smooth(ggplot2.aes_string(group = 'cyl'),
                         method = 'lm')
pp.plot()
#-- ggplot2smoothbycyl-end
grdevices.dev_off()

grdevices.png('../../_static/graphics_ggplot2_smoothbycylwithcolours.png',
              width = 612, height = 612, antialias="subpixel", type="cairo")
#-- ggplot2smoothbycylwithcolours-begin
pp = ggplot2.ggplot(mtcars) + \
     ggplot2.aes_string(x='wt', y='mpg', col='factor(cyl)') + \
     ggplot2.geom_point() + \
     ggplot2.geom_smooth(ggplot2.aes_string(group = 'cyl'),
                         method = 'lm')
pp.plot()
#-- ggplot2smoothbycylwithcolours-end
grdevices.dev_off()


grdevices.png('../../_static/graphics_ggplot2smoothbycylfacetcyl.png',
              width = 612, height = 612, antialias="subpixel", type="cairo")
#-- ggplot2smoothbycylfacetcyl-begin
pp = gp + \
     ggplot2.aes_string(x='wt', y='mpg') + \
     ggplot2.geom_point() + \
     ggplot2.facet_grid(ro.Formula('. ~ cyl')) + \
     ggplot2.geom_smooth(ggplot2.aes_string(group="cyl"),
                         method = "lm",
                            data = mtcars)

pp.plot()
#-- ggplot2smoothbycylfacetcyl-end
grdevices.dev_off()


grdevices.png('../../_static/graphics_ggplot2histogramfacetcyl.png',
              width = 612, height = 612, antialias="subpixel", type="cairo")
#-- ggplot2histogramfacetcyl-begin
pp = gp + \
     ggplot2.aes_string(x='wt') + \
     ggplot2.geom_histogram(binwidth=2) + \
     ggplot2.facet_grid(ro.Formula('. ~ cyl'))

pp.plot()
#-- ggplot2histogramfacetcyl-end
grdevices.dev_off()

grdevices.png('../../_static/graphics_ggplot2perfcolor_both.png',
              width = 900, height = 412, antialias="subpixel", type="cairo")
grid.newpage()
grid.viewport(layout=grid.layout(1, 2)).push()
#-- ggplot2perfcolor-begin
# set up data structures for mapping attributes to colors, line types, and 
#   labels
colormap_raw = [['red', '#ff0000'],
                ['green', '#76b900']]
colormap_labels = [['red', 'RED'],
                   ['green', 'GREEN']]
colormap = ro.StrVector([elt[1] for elt in colormap_raw])
colormap.names = ro.StrVector([elt[0] for elt in colormap_raw])

linemap_raw = [['Perf2', 'dashed'],
               ['Perf1', 'solid']]
linemap = ro.StrVector([elt[1] for elt in linemap_raw])
linemap.names = ro.StrVector([elt[0] for elt in linemap_raw])

# input data, which may normally come from an external csv file
# note the use of base.I which makes R interpret these as explicit data
#   rather than store them as factors; since we're manipulating them 
#   directly, we need them stored explicitly
input_dataframes = { 
   'red' : ro.DataFrame({ 'Date' : base.as_Date(ro.StrVector(("2008-06-25", "2009-09-23"))),
                          'Perf1' : ro.FloatVector((1090,2500)),
                          'Perf2' : ro.FloatVector((215,500))
                          }),
   'green' : ro.DataFrame({ 'Date' : base.as_Date(ro.StrVector(("2008-06-15", 
                                                                "2010-04-15"))),
                            'Perf1' : ro.FloatVector((922,1030)),
                            'Perf2' : ro.FloatVector((78,515))
                            })
   }

# create empty data frame df ...
df = ro.DataFrame({})
for color in ['green', 'red']:
  # ... then for each input data frame, read that data frame (perhaps
  # from a file), append column of color names, then append to df
  df = df.rbind(input_dataframes[color].
                cbind(ro.DataFrame({'color' : 
                                    base.I(ro.StrVector([color]))})))

# now do some data processing

# read out 'Date' column, convert using python dateutil parser, put
#   back into 'Date' column
# example of taking data in R dataframe, changing it in python, then
#   putting it back

#df[tuple(df.colnames).index('Date')] = \
#    base.as_Date(df.rx2('Date'))

# what is the range of Perf1 and Perf2? we use this for custom log plot lines
perfs = df[tuple(df.colnames).index('Perf1')] + \
        df[tuple(df.colnames).index('Perf2')]
gflops_range = [ round(math.log10(min(perfs))), 
                 round(math.log10(max(perfs))) ]

# we have data that looks like this:
# [date, perf1, perf2, color]
# note there's two measurements per line.
# instead we want data that looks like this:
# [date, perf, color, perftype] where perftype is perf1 or perf2
# the right operator for this is "melt" in the "reshape2" package

# melt from horizontal into vertical format
df = reshape2.melt(df, 
                   id_vars=['Date','color'], 
                   measure_vars=['Perf1','Perf2'], 
                   variable_name='PerfType')
# rename resulting value column to Performance
df.names[tuple(df.colnames).index('value')] = 'Performance'

# now we have 4 datasets: {red, green} x {perf1, perf2}
# plot the colored datasets in their respective colors
# plot the PerfTypes as solid (circle markers) and dashed (triangle markers) 
#   lines

# plot with both log and linear y scales
# aes_string: set the axis labels and what we're plotting
# opts: set the title and the thickness of the lines
#   note the use of **{} to allow setting "legend.key.size" as a keyword
# scale_colour_manual: associate color datasets with actual colors and names
# geom_point and geom_line: thicker points and lines
# scale_linetype_manual: associate perf types with linetypes
for col_i, yscale in enumerate(['log', 'linear']): 
  vp = grid.viewport(**{'layout.pos.col':col_i+1, 'layout.pos.row': 1})
  pp = ggplot2.ggplot(df) + \
      ggplot2.aes_string(x='variable', y='Performance', color='color', 
                         shape='PerfType', linetype='PerfType') + \
      ggplot2.opts(**{'title' : 
                      'Performance vs. Color',
                      'legend.key.size' : ro.r.unit(1.4, "lines") } ) + \
      ggplot2.scale_colour_manual("Color", 
                                  values=colormap,
                                  breaks=colormap.names,
                                  labels=[elt[1] for elt in 
                                          colormap_labels]) + \
      ggplot2.geom_point(size=3) + \
      ggplot2.scale_linetype_manual(values=linemap) + \
      ggplot2.geom_line(size=1.5)

  # custom y-axis lines: major lines ("breaks") are every 10^n; 9
  #   minor lines ("minor_breaks") between major lines
  if (yscale == 'log'):
    pp = pp + \
        ggplot2.scale_y_log10(breaks = ro.r("10^(%d:%d)" % (gflops_range[0], 
                                                            gflops_range[1])),
                              minor_breaks = 
                              ro.r("rep(10^(%d:%d), each=9) * rep(1:9, %d)" %
                                   (gflops_range[0] - 1, gflops_range[1], 
                                    gflops_range[1] - gflops_range[0])))

  #pp.plot(vp = vp)
#-- ggplot2perfcolor-end
grdevices.dev_off()



# grdevices.png('../../_static/graphics_ggplot2coordtranssqrt.png',
#               width = 612, height = 612)
# #-- ggplot2coordtranssqrt-begin
# pp = gp + \
#      ggplot2.aes_string(x='wt', y='mpg') + \
#      ggplot2.scale_y_sqrt() + \
#      ggplot2.geom_point()

# pp.plot()
# #-- ggplot2coordtranssqrt-end
# grdevices.dev_off()

# grdevices.png('../../_static/graphics_ggplot2coordtransreverse.png',
#               width = 612, height = 612)
# #-- ggplot2coordtransreverse-begin
# pp = gp + \
#      ggplot2.aes_string(x='wt', y='mpg') + \
#      ggplot2.geom_point() + \
#      ggplot2.scale_y_reverse()

# pp.plot()
# #-- ggplot2coordtransreverse-end
# grdevices.dev_off()


grdevices.png('../../_static/graphics_ggplot2map_polygon.png',
              width = 612, height = 612, antialias="subpixel", type="cairo")
#-- ggplot2mappolygon-begin
map = importr('maps')
fr = ggplot2.map_data('france')

# add a column indicating which region names have an "o".
fr = fr.cbind(fr, has_o = base.grepl('o', fr.rx2("region"),
                                     ignore_case = True))
p = ggplot2.ggplot(fr) + \
    ggplot2.geom_polygon(ggplot2.aes(x = 'long', y = 'lat',
                                     group = 'group', fill = 'has_o'),
                         col="black")
p.plot()
#-- ggplot2mappolygon-end
grdevices.dev_off()




grdevices.png('../../_static/graphics_grid.png',
              width = 612, height = 612, antialias="subpixel", type="cairo")
#-- grid-begin
grid.newpage()
# create a rows/columns layout
lt = grid.layout(2, 3)
vp = grid.viewport(layout = lt)
# push it the plotting stack
vp.push()

# create a viewport located at (1,1) in the layout
vp = grid.viewport(**{'layout.pos.col':1, 'layout.pos.row': 1})
# create a (unit) rectangle in that viewport
grid.rect(vp = vp).draw()

vp = grid.viewport(**{'layout.pos.col':2, 'layout.pos.row': 2})
# create text in the viewport at (1,2)
grid.text("foo", vp = vp).draw()

vp = grid.viewport(**{'layout.pos.col':3, 'layout.pos.row': 1})
# create a (unit) circle in the viewport (1,3)
grid.circle(vp = vp).draw()

#-- grid-end
grdevices.dev_off()



grdevices.png('../../_static/graphics_ggplot2withgrid.png',
              width = 612, height = 612, antialias="subpixel", type="cairo")
#-- gridwithggplot2-begin
grid.newpage()

# create a viewport as the main plot
vp = grid.viewport(width = 1, height = 1) 
vp.push()

utils.data("rock", package = "datasets", envir = tmpenv)
rock = tmpenv["rock"]

p = ggplot2.ggplot(rock) + \
    ggplot2.geom_point(ggplot2.aes_string(x = 'area', y = 'peri')) + \
    ggplot2.theme_bw()
p.plot(vp = vp)

vp = grid.viewport(width = 0.6, height = 0.6, x = 0.37, y=0.69)
vp.push()
p = ggplot2.ggplot(rock) + \
    ggplot2.geom_point(ggplot2.aes_string(x = 'area', y = 'shape')) + \
    ggplot2.opts(**{'axis.text.x': ggplot2.theme_text(angle = 45)})

p.plot(vp = vp)

#-- gridwithggplot2-end
grdevices.dev_off()




#---

pp = gp + \
     ggplot2.aes_string(x='wt', y='mpg') + \
     ggplot2.geom_density(ggplot2.aes_string(group = 'cyl')) + \
     ggplot2.geom_point() + \
     ggplot2.facet_grid(ro.Formula('. ~ cyl'))

pp = gp + \
     ggplot2.aes_string(x='wt', y='mpg') + \
     ggplot2.facet_grid(ro.Formula('gear ~ cyl')) + \
     ggplot2.geom_point()




pp = gp + \
     ggplot2.aes_string(x='mpg') + \
     ggplot2.FacetGrid.new(ro.Formula('. ~ cyl')) + \
     ggplot2.GeomHistogram.new(binwidth = 5)
