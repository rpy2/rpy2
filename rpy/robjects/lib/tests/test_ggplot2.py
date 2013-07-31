import unittest

# Try to load R ggplot package, and see if it works
from rpy2.rinterface import RRuntimeError
has_ggplot = True
try:
    from rpy2.robjects.lib import ggplot2
except RRuntimeError:
    has_ggplot = False

from rpy2.robjects.packages import importr
datasets = importr('datasets')
mtcars = datasets.__rdata__.fetch('mtcars')['mtcars']

@unittest.skipUnless(has_ggplot, 'ggplot2 package not available in R')
class GGPlot2TestCase(unittest.TestCase):

    def testSetup(self):
        pass

    def tearDown(self):
        pass

    def testGGPlot(self):
        gp = ggplot2.ggplot(mtcars)
        self.assertTrue(isinstance(gp, ggplot2.GGPlot))

    def testAdd(self):
        gp = ggplot2.ggplot(mtcars)
        pp = gp + \
            ggplot2.aes_string(x='wt', y='mpg') + \
            ggplot2.geom_point()
        self.assertTrue(isinstance(pp, ggplot2.GGPlot))

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(GGPlot2TestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
