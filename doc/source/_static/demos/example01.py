"""
short demo.

"""

import rpy2.robjects as robjects
import array

r = robjects.r

x = array.array('i', range(10))
y = r.rnorm(10)

r.X11()

r.par(mfrow=array.array('i', [2,2]))
r.plot(x, y, ylab="foo/bar", col="red")

kwargs = {'ylab':"foo/bar", 'type':"b", 'col':"blue", 'log':"x"}
r.plot(x, y, **kwargs)


m = r.matrix(r.rnorm(100), ncol=5)
pca = r.princomp(m)
r.plot(pca, main="Eigen values")
r.biplot(pca, main="biplot")


if not r.require("GO.db")[0]:
    raise(Exception("Bioconductor Package GO missing"))


goItem = r.GOTERM["GO:0000001"]


