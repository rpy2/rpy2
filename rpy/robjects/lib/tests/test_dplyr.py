import unittest

# Try to load R dplyr package, and see if it works
from rpy2.rinterface import RRuntimeError
has_dplyr = None
try:
    from rpy2.robjects.lib import dplyr
    has_dplyr = True
except RRuntimeError:
    has_dplyr = False

from rpy2.robjects.packages import importr, data
datasets = importr('datasets')
mtcars = data(datasets).fetch('mtcars')['mtcars']

@unittest.skipUnless(has_dplyr, 'dplyr package not available in R')
class DplyrTestCase(unittest.TestCase):

    def testSetup(self):
        pass

    def tearDown(self):
        pass

    def testDataFrame(self):
        dataf = dplyr.DataFrame(mtcars)
        # FIXME: no testing much at the moment...
        self.assertTrue(isinstance(dataf, dplyr.DataFrame))

    def testFilter_NoFilter(self):
        dataf = dplyr.DataFrame(mtcars)
        dataf_filter = dataf.filter()
        self.assertEqual(dataf.nrow, dataf_filter.nrow)

    def testFilter_OneFilter(self):
        dataf = dplyr.DataFrame(mtcars)
        ngear_gt_3 = len(tuple(x for x in dataf.rx2('gear') if x > 3))
        dataf_filter = dataf.filter('gear > 3')        
        self.assertEqual(ngear_gt_3, dataf_filter.nrow)

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(DplyrTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
