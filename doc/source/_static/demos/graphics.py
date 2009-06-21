
#-- setup-begin
from rpy2 import robjects
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

formula = robjects.RFormula('mpg ~ wt')
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
formula = robjects.RFormula('mpg ~ wt | cyl')
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
gp = ggplot2.GGPlot.new(mtcars)

pp = gp + \
     ggplot2.Aes.new(x='wt', y='mpg') + \
     ggplot2.GeomPoint.new()

pp.plot()
#-- ggplot2mtcars-end
grdevices.dev_off()

grdevices.png('../../_static/graphics_ggplot2mtcarscolcyl.png',
    width = 512, height = 512)
#-- ggplot2mtcarscolcyl-begin
gp = ggplot2.GGPlot.new(mtcars)

pp = gp + \
     ggplot2.Aes.new(x='wt', y='mpg', col='cyl') + \
     ggplot2.GeomPoint.new()

pp.plot()
#-- ggplot2mtcarscolcyl-end
grdevices.dev_off()


grdevices.png('../../_static/graphics_ggplot2_ggplot_1.png',
              width = 512, height = 512)
#-- ggplot1-begin
pp = gp + \
     ggplot2.Aes.new(x='wt', y='mpg') + \
     ggplot2.GeomPoint.new() + \
     ggplot2.FacetGrid.new(ro.RFormula('. ~ cyl'))


pp.plot()
#-- ggplot1-end
grdevices.dev_off()



grdevices.png('../../_static/graphics_ggplot2aescolsize.png',
              width = 512, height = 512)
#-- ggplot2aescolsize-begin
pp = gp + \
     ggplot2.Aes.new(x='wt', y='mpg', size='gear', col='cyl') + \
     ggplot2.GeomPoint.new()

pp.plot()
#-- ggplot2aescolsize-end
grdevices.dev_off()

grdevices.png('../../_static/graphics_ggplot2_qplot_4.png',
              width = 512, height = 512)
#-- qplot4-begin
pp = gp + \
     ggplot2.Aes.new(x='wt', y='mpg') + \
     ggplot2.GeomPoint.new() + \
     ggplot2.GeomAbline.new(intercept = 30)
pp.plot()
#-- qplot4-end
grdevices.dev_off()

grdevices.png('../../_static/graphics_ggplot2_qplot_5.png',
              width = 512, height = 512)
#-- qplot3addline-begin
pp = gp + \
     ggplot2.Aes.new(x='wt', y='mpg') + \
     ggplot2.GeomPoint.new() + \
     ggplot2.GeomAbline.new(intercept = 30) + \
     ggplot2.GeomAbline.new(intercept = 15)
pp.plot()
#-- qplot3addline-end
grdevices.dev_off()


grdevices.png('../../_static/graphics_ggplot2_qplot_6.png',
              width = 512, height = 512)
#-- qplot3addsmooth-begin
pp = gp + \
     ggplot2.Aes.new(x='wt', y='mpg') + \
     ggplot2.GeomPoint.new() + \
     ggplot2.StatSmooth.new(method = 'lm')
pp.plot()

#-- qplot3addsmooth-end
grdevices.dev_off()


grdevices.png('../../_static/graphics_ggplot2smoothblue.png',
              width = 512, height = 512)
#-- ggplot2smoothblue-begin
pp = gp + \
     ggplot2.Aes.new(x='wt', y='mpg') + \
     ggplot2.GeomPoint.new() + \
     ggplot2.StatSmooth.new(method = 'lm', fill = 'blue',
                            color = 'red', size = 3)
pp.plot()
#-- ggplot2smoothblue-end
grdevices.dev_off()

grdevices.png('../../_static/graphics_ggplot2smoothbycyl.png',
              width = 512, height = 512)
#-- ggplot2smoothbycyl-begin
pp = gp + \
     ggplot2.Aes.new(x='wt', y='mpg') + \
     ggplot2.GeomPoint.new() + \
     ggplot2.GeomSmooth.new(ggplot2.Aes.new(group = 'cyl'),
                            method = 'lm')
pp.plot()
#-- ggplot2smoothbycyl-end
grdevices.dev_off()

grdevices.png('../../_static/graphics_ggplot2_smoothbycylwithcolours.png',
              width = 512, height = 512)
#-- ggplot2smoothbycylwithcolours-begin
pp = gp + \
     ggplot2.Aes.new(x='wt', y='mpg') + \
     ggplot2.GeomPoint.new() + \
     ggplot2.GeomSmooth.new(ggplot2.Aes.new(group = 'cyl'),
                            method = 'lm')
pp.plot()
#-- ggplot2smoothbycylwithcolours-end
grdevices.dev_off()


grdevices.png('../../_static/graphics_ggplot2smoothbycylfacetcyl.png',
              width = 512, height = 512)
#-- ggplot2smoothbycylfacetcyl-begin
pp = gp + \
     ggplot2.Aes.new(x='wt', y='mpg') + \
     ggplot2.GeomPoint.new() + \
     ggplot2.FacetGrid.new(ro.RFormula('. ~ cyl')) + \
     ggplot2.GeomSmooth.new(ggplot2.Aes.new(group="cyl"),
                            method = "lm",
                            data = mtcars)

pp.plot()
#-- ggplot2smoothbycylfacetcyl-end
grdevices.dev_off()


grdevices.png('../../_static/graphics_ggplot2histogramfacetcyl.png',
              width = 512, height = 512)
#-- ggplot2histogramfacetcyl-begin
pp = gp + \
     ggplot2.Aes.new(x='wt') + \
     ggplot2.GeomHistogram.new(binwidth=2) + \
     ggplot2.FacetGrid.new(ro.RFormula('. ~ cyl'))

pp.plot()
#-- ggplot2histogramfacetcyl-end
grdevices.dev_off()



#---

pp = gp + \
     ggplot2.Aes.new(x='wt', y='mpg') + \
     ggplot2.GeomDensity2D.new(ggplot2.Aes.new(group="cyl")) + \
     ggplot2.GeomPoint.new() + \
     ggplot2.FacetGrid.new(ro.RFormula('. ~ cyl'))

pp = gp + \
     ggplot2.Aes.new(x='wt', y='mpg') + \
     ggplot2.FacetGrid.new(ro.RFormula('gear ~ cyl')) + \
     ggplot2.GeomPoint.new()




pp = gp + \
     ggplot2.Aes.new(x='mpg') + \
     ggplot2.FacetGrid.new(ro.RFormula('. ~ cyl')) + \
     ggplot2.GeomHistogram.new(binwidth = 5)
