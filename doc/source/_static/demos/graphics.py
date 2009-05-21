#--line 1
from rpy2 import robjects

# import an R package
def rimport(x):
   robjects.baseenv["require"](x, quietly = True)

# load an R dataset
data = robjects.baseenv.get("data")

# The R 'print' function
rprint = robjects.globalenv.get("print")
#--line 13

#--line 15
rimport('lattice')

xyplot = robjects.baseenv.get("xyplot")
#--line 19

grdevices_env = robjects.baseenv['as.environment']('package:grDevices')
png = grdevices_env['png']
dev_off = grdevices_env['dev.off']

png('../../_static/graphics_lattice_xyplot_1.png',
    width = 480, height = 480)
#--line 27
data("mtcars")
mtcars = robjects.globalenv["mtcars"]

xyplot = robjects.baseenv.get('xyplot')

formula = robjects.RFormula('mpg ~ wt')
formula.getenvironment()['mpg'] = mtcars.r['mpg'][0]
formula.getenvironment()['wt'] = mtcars.r['wt'][0]

p = xyplot(formula)
rprint(p)
#--line 39
dev_off()

png('../../_static/graphics_lattice_xyplot_2.png',
    width = 480, height = 480)
#--line 44
p = xyplot(formula, groups = mtcars.r['cyl'][0])
rprint(p)
#--line 47
dev_off()

png('../../_static/graphics_lattice_xyplot_3.png',
    width = 480, height = 480)
#--line 52
formula = robjects.RFormula('mpg ~ wt | cyl')
formula.getenvironment()['mpg'] = mtcars.r['mpg'][0]
formula.getenvironment()['wt'] = mtcars.r['wt'][0]
formula.getenvironment()['cyl'] = mtcars.r['cyl'][0]

p = xyplot(formula, layout=robjects.IntVector((3, 1)))
rprint(p)
#--line 60
dev_off()


#--line 64
rimport("ggplot2")

def dparse(x):
   res = robjects.baseenv["parse"](text = x)
   return res
#--line 70


png('../../_static/graphics_ggplot2_qplot_1.png',
    width = 480, height = 480)
#--line 72
qplot = robjects.r["qplot"]

x = robjects.r.rnorm(5)
y = x + robjects.r.rnorm(5, sd = 0.2)
xy = qplot(x, y, xlab="x", ylab="y")

rprint(xy)
#--line 80
dev_off()

png('../../_static/graphics_ggplot2_qplot_2.png',
    width = 480, height = 480)
#--line 88
data("mtcars")
mtcars = robjects.globalenv["mtcars"]

xy = qplot(dparse("wt"), dparse("mpg"), 
           data = mtcars,
           xlab = "wt", ylab = "mpg")

rprint(xy)
#--line 97
dev_off()


png('../../_static/graphics_ggplot2_ggplot_1.png',
    width = 480, height = 480)
#--line 103
def radd(x, y):
    res = robjects.baseenv.get("+")(x, y)
    return res

ggplot = robjects.globalenv.get("ggplot")
aes = robjects.globalenv.get("aes")

xy = ggplot(mtcars, aes(y = dparse('wt'), x = dparse('mpg')))

facet_grid = robjects.globalenv.get("facet_grid")
p = radd(xy, facet_grid(robjects.RFormula('. ~ cyl')))

geom_point = robjects.globalenv.get("geom_point")
p = radd(p, geom_point())

rprint(p)
#--line 120
dev_off()


png('../../_static/graphics_ggplot2_qplot_3.png',
    width = 480, height = 480)
#--line 126
geom_abline = robjects.globalenv.get("geom_abline")

xy = qplot(dparse("wt"), dparse("mpg"), 
           data = mtcars,
           xlab = "wt", ylab = "mpg")

line = geom_abline(intercept = 30) 
p = radd(xy, line)
rprint(p)
#--line 136
dev_off()

png('../../_static/graphics_ggplot2_qplot_4.png',
    width = 480, height = 480)
#--line 141
p = radd(p, geom_abline(intercept = 15))
rprint(p)
#--line 144
dev_off()


png('../../_static/graphics_ggplot2_qplot_5.png',
    width = 480, height = 480)
#--line 150
stat_smooth = robjects.globalenv.get("stat_smooth")

p = radd(xy, stat_smooth(method = "lm"))
rprint(p)
#--line 155
dev_off()


png('../../_static/graphics_ggplot2_qplot_6.png',
    width = 480, height = 480)
#--line 161
p = radd(xy, stat_smooth(method = "lm", 
                         fill="blue", colour="#e03030d0", size=3))
rprint(p)
#--line 165
dev_off()

png('../../_static/graphics_ggplot2_qplot_7.png',
    width = 480, height = 480)
#--line 170
geom_smooth = robjects.globalenv.get("geom_smooth")
p = radd(xy, geom_smooth(aes(group=dparse("cyl")), method = "lm"))
rprint(p)
#--line 174
dev_off()


png('../../_static/graphics_ggplot2_ggplot_add.png',
    width = 480, height = 480)
#--line 180
xy = ggplot(mtcars, aes(y = dparse('wt'), x = dparse('mpg')))
facet_grid = robjects.globalenv.get("facet_grid")
p = radd(xy, geom_point())
p = radd(p, facet_grid(robjects.RFormula('. ~ cyl')))
p = radd(p, geom_smooth(aes(group=dparse("cyl")), method = "lm", data = mtcars))
rprint(p)
#--line 186
dev_off()

