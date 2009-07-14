
#-- setup-begin
from rpy2 import robjects
from rpy2.robjects.lib import grid
from rpy2.robjects.lib import grdevices


# import an R package
def rimport(x):
   robjects.baseenv["require"](x, quietly = True)

# load an R dataset
data = robjects.baseenv.get("data")

# The R 'print' function
rprint = robjects.globalenv.get("print")
#-- setup-end

#-- setuplattice-begin
rimport('lattice')
#-- setuplattice-end
#-- setupxyplot-begin
xyplot = robjects.baseenv.get("xyplot")
#-- setupxyplot-end

grdevices.png('../../_static/graphics_lattice_xyplot_1.png',
    width = 512, height = 512)
#-- xyplot1-begin
data("mtcars")
mtcars = robjects.globalenv["mtcars"]

xyplot = robjects.baseenv.get('xyplot')

formula = robjects.Formula('mpg ~ wt')
formula.getenvironment()['mpg'] = mtcars.rx2('mpg')
formula.getenvironment()['wt'] = mtcars.rx2('wt')

p = xyplot(formula)
rprint(p)
#-- xyplot1-end
grdevices.dev_off()

grdevices.png('../../_static/graphics_lattice_xyplot_2.png',
    width = 512, height = 512)
#-- xyplot2-begin
p = xyplot(formula, groups = mtcars.rx2('cyl'))
rprint(p)
#-- xyplot2-end
grdevices.dev_off()

grdevices.png('../../_static/graphics_lattice_xyplot_3.png',
    width = 512, height = 512)
#-- xyplot3-begin
formula = robjects.Formula('mpg ~ wt | cyl')
formula.getenvironment()['mpg'] = mtcars.rx2('mpg')
formula.getenvironment()['wt'] = mtcars.rx2('wt')
formula.getenvironment()['cyl'] = mtcars.rx2('cyl')

p = xyplot(formula, layout=robjects.IntVector((3, 1)))
rprint(p)
#-- xyplot3-end
grdevices.dev_off()


#-- setupggplot2-begin
import rpy2.robjects.lib.ggplot2 as ggplot2
import rpy2.robjects as ro
ro.r.data("mtcars")
mtcars = ro.r("mtcars")
#-- setupggplot2-end

grdevices.png('../../_static/graphics_ggplot2mtcars.png',
    width = 512, height = 512)
#-- ggplot2mtcars-begin
gp = ggplot2.ggplot(mtcars)

pp = gp + \
     ggplot2.aes(x='wt', y='mpg') + \
     ggplot2.geom_point()

pp.plot()
#-- ggplot2mtcars-end
grdevices.dev_off()

grdevices.png('../../_static/graphics_ggplot2geombin2d.png',
    width = 512, height = 512)
#-- ggplot2geombin2d-begin
gp = ggplot2.ggplot(mtcars)

pp = gp + \
     ggplot2.aes(x='wt', y='mpg') + \
     ggplot2.geom_bin2d()

pp.plot()
#-- ggplot2geombin2d-end
grdevices.dev_off()

grdevices.png('../../_static/graphics_ggplot2geomboxplot.png',
    width = 512, height = 512)
#-- ggplot2geomboxplot-begin
gp = ggplot2.ggplot(mtcars)

pp = gp + \
     ggplot2.aes(x='factor(cyl)', y='mpg') + \
     ggplot2.geom_boxplot()

pp.plot()
#-- ggplot2geomboxplot-end
grdevices.dev_off()


#-- ggplot2geomhistogram-begin
gp = ggplot2.ggplot(mtcars)

pp = gp + \
     ggplot2.aes(x='wt') + \
     ggplot2.geom_histogram()

pp.plot()
#-- ggplot2geomhistogram-end

grdevices.png('../../_static/graphics_ggplot2geomhistogram.png',
    width = 900, height = 412)
grid.newpage()
grid.viewport(layout=grid.layout(1, 3)).push()

params = (('black', 'black'),
          ('black', 'white'),
          ('white', 'black'))
          
for col_i in range(3):
   vp = grid.viewport(**{'layout.pos.col':col_i+1, 'layout.pos.row': 1})
   outline_color, fill_color= params[col_i]
   pp = gp + \
        ggplot2.aes(x='wt') + \
        ggplot2.geom_histogram(col=outline_color, fill=fill_color) + \
        ggplot2.opts(title =  'col=%s - fill=%s' %params[col_i])
   ro.r['print'](pp, vp = vp)
grdevices.dev_off()

grdevices.png('../../_static/graphics_ggplot2geomhistogramfillcyl.png',
    width = 512, height = 512)
#-- ggplot2geomhistogramfillcyl-begin
gp = ggplot2.ggplot(mtcars)

pp = gp + \
     ggplot2.aes(x='wt', fill='factor(cyl)') + \
     ggplot2.geom_histogram()

pp.plot()
#-- ggplot2geomhistogramfillcyl-end
grdevices.dev_off()


grdevices.png('../../_static/graphics_ggplot2geomfreqpolyfillcyl.png',
    width = 812, height = 412)
grid.newpage()
grid.viewport(layout=grid.layout(1, 2)).push()

dataf = robjects.r['data.frame'](**{'value': robjects.r['rnorm'](100, mean=0) + robjects.r['rnorm'](100, mean=1), 
                                    'mean': robjects.r('rep(c(0,1), each=100)')})
gp = ggplot2.ggplot(dataf)

vp = grid.viewport(**{'layout.pos.col':1, 'layout.pos.row': 1})
pp = gp + \
     ggplot2.aes(x='value', col='factor(mean)') + \
     ggplot2.geom_freqpoly()
ro.r['print'](pp, vp = vp)

vp = grid.viewport(**{'layout.pos.col':2, 'layout.pos.row': 1})
#-- ggplot2geomfreqpolyfillcyl-begin
pp = gp + \
     ggplot2.aes(x='value', fill='factor(mean)', alpha=0.5) + \
     ggplot2.geom_density()
#-- ggplot2geomfreqpolyfillcyl-end
ro.r['print'](pp, vp = vp)

grdevices.dev_off()




grdevices.png('../../_static/graphics_ggplot2geompointandrug.png',
    width = 512, height = 512)
#-- ggplot2geompointandrug-begin
gp = ggplot2.ggplot(mtcars)

pp = gp + \
     ggplot2.aes(x='wt', y='mpg') + \
     ggplot2.geom_point() + \
     ggplot2.geom_rug()

pp.plot()
#-- ggplot2geompointandrug-end
grdevices.dev_off()



grdevices.png('../../_static/graphics_ggplot2mtcarscolcyl.png',
    width = 512, height = 512)
#-- ggplot2mtcarscolcyl-begin
gp = ggplot2.ggplot(mtcars)

pp = gp + \
     ggplot2.aes(x='wt', y='mpg', col='factor(cyl)') + \
     ggplot2.geom_point()

pp.plot()
#-- ggplot2mtcarscolcyl-end
grdevices.dev_off()


grdevices.png('../../_static/graphics_ggplot2_ggplot_1.png',
              width = 512, height = 512)
#-- ggplot1-begin
pp = gp + \
     ggplot2.aes(x='wt', y='mpg') + \
     ggplot2.geom_point() + \
     ggplot2.facet_grid(ro.Formula('. ~ cyl'))


pp.plot()
#-- ggplot1-end
grdevices.dev_off()



grdevices.png('../../_static/graphics_ggplot2aescolsize.png',
              width = 512, height = 512)
#-- ggplot2aescolsize-begin
pp = gp + \
     ggplot2.aes(x='wt', y='mpg', size='factor(carb)',
                 col='factor(cyl)', shape='factor(gear)') + \
     ggplot2.geom_point()

pp.plot()
#-- ggplot2aescolsize-end
grdevices.dev_off()

grdevices.png('../../_static/graphics_ggplot2aescolboxplot.png',
              width = 512, height = 512)
#-- ggplot2aescolboxplot-begin
gp = ggplot2.ggplot(mtcars)

pp = gp + \
     ggplot2.aes(x='factor(cyl)', y='mpg', fill='factor(cyl)') + \
     ggplot2.geom_boxplot()

pp.plot()
#-- ggplot2aescolboxplot-end
grdevices.dev_off()




grdevices.png('../../_static/graphics_ggplot2_qplot_4.png',
              width = 512, height = 512)
#-- qplot4-begin
pp = gp + \
     ggplot2.aes(x='wt', y='mpg') + \
     ggplot2.geom_point() + \
     ggplot2.geom_abline(intercept = 30)
pp.plot()
#-- qplot4-end
grdevices.dev_off()

grdevices.png('../../_static/graphics_ggplot2_qplot_5.png',
              width = 512, height = 512)
#-- qplot3addline-begin
pp = gp + \
     ggplot2.aes(x='wt', y='mpg') + \
     ggplot2.geom_point() + \
     ggplot2.geom_abline(intercept = 30) + \
     ggplot2.geom_abline(intercept = 15)
pp.plot()
#-- qplot3addline-end
grdevices.dev_off()


grdevices.png('../../_static/graphics_ggplot2addsmooth.png',
              width = 512, height = 512)
#-- ggplot2addsmooth-begin
pp = gp + \
     ggplot2.aes(x='wt', y='mpg') + \
     ggplot2.geom_point() + \
     ggplot2.stat_smooth(method = 'lm')
pp.plot()

#-- ggplot2addsmooth-end
grdevices.dev_off()


grdevices.png('../../_static/graphics_ggplot2addsmoothmethods.png',
              width = 1024, height = 340)

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
        ggplot2.aes(x='wt', y='mpg') + \
        ggplot2.geom_point() + \
        ggplot2.stat_smooth(method = method, formula=formula) + \
        ggplot2.opts(title = method + ' - ' + formula)
   ro.r['print'](pp, vp = vp)

#-- ggplot2addsmoothmethods-end
grdevices.dev_off()



grdevices.png('../../_static/graphics_ggplot2smoothblue.png',
              width = 512, height = 512)
#-- ggplot2smoothblue-begin
pp = gp + \
     ggplot2.aes(x='wt', y='mpg') + \
     ggplot2.geom_point() + \
     ggplot2.stat_smooth(method = 'lm', fill = 'blue',
                         color = 'red', size = 3)
pp.plot()
#-- ggplot2smoothblue-end
grdevices.dev_off()

grdevices.png('../../_static/graphics_ggplot2smoothbycyl.png',
              width = 512, height = 512)
#-- ggplot2smoothbycyl-begin
pp = gp + \
     ggplot2.aes(x='wt', y='mpg') + \
     ggplot2.geom_point() + \
     ggplot2.geom_smooth(ggplot2.Aes.new(group = 'cyl'),
                         method = 'lm')
pp.plot()
#-- ggplot2smoothbycyl-end
grdevices.dev_off()

grdevices.png('../../_static/graphics_ggplot2_smoothbycylwithcolours.png',
              width = 512, height = 512)
#-- ggplot2smoothbycylwithcolours-begin
pp = gp + \
     ggplot2.aes(x='wt', y='mpg', col='factor(cyl)') + \
     ggplot2.geom_point() + \
     ggplot2.geom_smooth(ggplot2.aes(group = 'cyl'),
                         method = 'lm')
pp.plot()
#-- ggplot2smoothbycylwithcolours-end
grdevices.dev_off()


grdevices.png('../../_static/graphics_ggplot2smoothbycylfacetcyl.png',
              width = 512, height = 512)
#-- ggplot2smoothbycylfacetcyl-begin
pp = gp + \
     ggplot2.aes(x='wt', y='mpg') + \
     ggplot2.geom_point() + \
     ggplot2.facet_grid(ro.Formula('. ~ cyl')) + \
     ggplot2.geom_smooth(ggplot2.aes(group="cyl"),
                         method = "lm",
                            data = mtcars)

pp.plot()
#-- ggplot2smoothbycylfacetcyl-end
grdevices.dev_off()


grdevices.png('../../_static/graphics_ggplot2histogramfacetcyl.png',
              width = 512, height = 512)
#-- ggplot2histogramfacetcyl-begin
pp = gp + \
     ggplot2.aes(x='wt') + \
     ggplot2.geom_histogram(binwidth=2) + \
     ggplot2.facet_grid(ro.Formula('. ~ cyl'))

pp.plot()
#-- ggplot2histogramfacetcyl-end
grdevices.dev_off()


# grdevices.png('../../_static/graphics_ggplot2coordtranssqrt.png',
#               width = 512, height = 512)
# #-- ggplot2coordtranssqrt-begin
# pp = gp + \
#      ggplot2.aes(x='wt', y='mpg') + \
#      ggplot2.scale_y_sqrt() + \
#      ggplot2.geom_point()

# pp.plot()
# #-- ggplot2coordtranssqrt-end
# grdevices.dev_off()

# grdevices.png('../../_static/graphics_ggplot2coordtransreverse.png',
#               width = 512, height = 512)
# #-- ggplot2coordtransreverse-begin
# pp = gp + \
#      ggplot2.aes(x='wt', y='mpg') + \
#      ggplot2.geom_point() + \
#      ggplot2.scale_y_reverse()

# pp.plot()
# #-- ggplot2coordtransreverse-end
# grdevices.dev_off()






#---

pp = gp + \
     ggplot2.aes(x='wt', y='mpg') + \
     ggplot2.geom_density(ggplot2.aes(group = 'cyl')) + \
     ggplot2.geom_point() + \
     ggplot2.facet_grid(ro.Formula('. ~ cyl'))

pp = gp + \
     ggplot2.aes(x='wt', y='mpg') + \
     ggplot2.facet_grid(ro.Formula('gear ~ cyl')) + \
     ggplot2.geom_point()




pp = gp + \
     ggplot2.Aes.new(x='mpg') + \
     ggplot2.FacetGrid.new(ro.Formula('. ~ cyl')) + \
     ggplot2.GeomHistogram.new(binwidth = 5)
