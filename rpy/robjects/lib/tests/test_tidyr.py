import unittest

# Try to load R dplyr package, and see if it works
has_tidyr = None
try:
    from rpy2.robjects.lib import tidyr
    has_tidyr = True
except RRuntimeError:
    has_tidyr = False

from rpy2.robjects import vectors
from rpy2.robjects.packages import (importr,
                                    data)
datasets = importr('datasets')
mtcars = data(datasets).fetch('mtcars')['mtcars']

@unittest.skipUnless(has_tidyr, 'tidyr package not available in R')
class TidyrTestCase(unittest.TestCase):


    def testDataFrame(self):
        dataf =tidyr.DataFrame(
            {'x': vectors.IntVector((1,2,3,4,5)),
             'labels': vectors.StrVector(('a','b','b','b','a'))})
        self.assertIsInstance(dataf, tidyr.DataFrame)
        self.assertCountEqual(('x', 'labels'), dataf.colnames)
        
    def testSpread(self):
        labels = ('a','b','c','d','e')
        dataf =tidyr.DataFrame(
            {'x': vectors.IntVector((1,2,3,4,5)),
             'labels': vectors.StrVector(labels)})
        dataf_spread = dataf.spread('labels', 'x')
        self.assertCountEqual(labels, dataf_spread.colnames)

    @unittest.expectedFailure
    def testGather(self):
        dataf =tidyr.DataFrame({'a': 1.0, 'b': 2.0})
        dataf_gathered = dataf.gather('label', 'x')
        self.assertCountEqual(('label', 'x'), dataf_gathered.colnames)

        
def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(TidyrTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
