#-- setup-begin
from rpy2 import robjects

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

grdevices_env = robjects.baseenv['as.environment']('package:grDevices')
png = grdevices_env['png']
dev_off = grdevices_env['dev.off']

png('../../_static/graphics_lattice_xyplot_1.png',
    width = 480, height = 480)
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
dev_off()

png('../../_static/graphics_lattice_xyplot_2.png',
    width = 480, height = 480)
#-- xyplot2-begin
p = xyplot(formula, groups = mtcars.rx2('cyl'))
rprint(p)
#-- xyplot2-end
dev_off()

png('../../_static/graphics_lattice_xyplot_3.png',
    width = 480, height = 480)
#-- xyplot3-begin
formula = robjects.RFormula('mpg ~ wt | cyl')
formula.getenvironment()['mpg'] = mtcars.rx2('mpg')
formula.getenvironment()['wt'] = mtcars.rx2('wt')
formula.getenvironment()['cyl'] = mtcars.rx2('cyl')

p = xyplot(formula, layout=robjects.IntVector((3, 1)))
rprint(p)
#-- xyplot3-end
dev_off()


#-- setupggplot2-begin
rimport("ggplot2")

def as_symbol(x):
   res = robjects.baseenv["parse"](text = x)
   return res[0]
#-- setupggplot2-end


png('../../_static/graphics_ggplot2_qplot_1.png',
    width = 480, height = 480)
#-- qplot1-begin
qplot = robjects.r["qplot"]

x = robjects.r.rnorm(5)
y = x + robjects.r.rnorm(5, sd = 0.2)
xy = qplot(x, y, xlab="x", ylab="y")
rprint(xy)
#-- qplot1-end
dev_off()

png('../../_static/graphics_ggplot2_qplot_2.png',
    width = 480, height = 480)
#-- qplot2-begin
data("mtcars")
mtcars = robjects.globalenv["mtcars"]

xy = qplot(as_symbol("wt"), as_symbol("mpg"), 
           data = mtcars,
           xlab = "wt", ylab = "mpg")

rprint(xy)
#-- qplot2-end
dev_off()

png('../../_static/graphics_ggplot2_qplot_3.png',
    width = 480, height = 480)
#-- qplot3-begin
data("mtcars")
mtcars = robjects.globalenv["mtcars"]

xy = qplot(as_symbol("wt"), as_symbol("mpg"), 
           data = mtcars, colour = as_symbol("cyl"),
           xlab = "wt", ylab = "mpg")

rprint(xy)
#-- qplot3-end
dev_off()


png('../../_static/graphics_ggplot2_ggplot_1.png',
    width = 480, height = 480)
#-- ggplot1-begin
ggplot = robjects.globalenv.get("ggplot")
aes = robjects.globalenv.get("aes")

xy = ggplot(mtcars, aes(y = as_symbol('wt'), x = as_symbol('mpg')))

facet_grid = robjects.globalenv.get("facet_grid")
p = xy.ro + facet_grid(robjects.RFormula('. ~ cyl'))

geom_point = robjects.globalenv.get("geom_point")
p = p.ro + geom_point()

rprint(p)
#-- ggplot1-end
dev_off()


png('../../_static/graphics_ggplot2_qplot_4.png',
    width = 480, height = 480)
#-- qplot4-begin
geom_abline = robjects.globalenv.get("geom_abline")

xy = qplot(as_symbol("wt"), as_symbol("mpg"), 
           data = mtcars,
           xlab = "wt", ylab = "mpg")

line = geom_abline(intercept = 30) 
p = xy.ro + line
rprint(p)
#-- qplot4-end
dev_off()

png('../../_static/graphics_ggplot2_qplot_5.png',
    width = 480, height = 480)
#-- qplot3addline-begin
p = p.ro + geom_abline(intercept = 15)
rprint(p)
#-- qplot3addline-end
dev_off()


png('../../_static/graphics_ggplot2_qplot_6.png',
    width = 480, height = 480)
#-- qplot3addsmooth-begin
stat_smooth = robjects.globalenv.get("stat_smooth")

p = xy.ro + stat_smooth(method = "lm")
rprint(p)
#-- qplot3addsmooth-end
dev_off()


png('../../_static/graphics_ggplot2_qplot_7.png',
    width = 480, height = 480)
#-- qplot3addsmoothblue-begin
p = xy.ro + stat_smooth(method = "lm", 
                        fill="blue", colour="#e03030d0", size=3)
rprint(p)
#-- qplot3addsmoothblue-end
dev_off()

png('../../_static/graphics_ggplot2_qplot_7.png',
    width = 480, height = 480)
#-- ggplot1addsmooth-begin
geom_smooth = robjects.globalenv.get("geom_smooth")
p = xy.ro + geom_smooth(aes(group=as_symbol("cyl")), method = "lm")
rprint(p)
#-- ggplot1addsmooth-end
dev_off()


png('../../_static/graphics_ggplot2_ggplot_add.png',
    width = 480, height = 480)
#-- ggplot2-begin
xy = ggplot(mtcars, aes(y = as_symbol('wt'), x = as_symbol('mpg')))
facet_grid = robjects.globalenv.get("facet_grid")
p = xy.ro + geom_point()
p = p.ro + facet_grid(robjects.RFormula('. ~ cyl'))
p = p.ro + geom_smooth(aes(group=as_symbol("cyl")),
                       method = "lm",
                       data = mtcars)
rprint(p)
#-- ggplot2-end
dev_off()


png('../../_static/graphics_ggplot2_ggplot_addtwo.png',
    width = 480, height = 480)
#-- ggplot2-begin
xy = ggplot(mtcars, aes(y = as_symbol('wt'), x = as_symbol('mpg')))
facet_grid = robjects.globalenv.get("facet_grid")
p = xy.ro + geom_point()
p = p.ro + facet_grid(robjects.RFormula('gear ~ cyl'))
p = p.ro + geom_smooth(aes(group=as_symbol("cyl")),
                       method = "lm",
                       data = mtcars)
rprint(p)
#-- ggplot2-end
dev_off()

