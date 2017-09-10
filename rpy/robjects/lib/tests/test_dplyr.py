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

    def testFilter_NoFilter_Method(self):
        dataf = dplyr.DataFrame(mtcars)
        dataf_filter = dataf.filter()
        self.assertEqual(dataf.nrow, dataf_filter.nrow)

    def testFilter_NoFilter_Function(self):
        dataf = dplyr.DataFrame(mtcars)
        dataf_filter = dplyr.filter(dataf)
        self.assertEqual(dataf.nrow, dataf_filter.nrow)
        
    def testFilter_OneFilter_Method(self):
        dataf = dplyr.DataFrame(mtcars)
        ngear_gt_3 = len(tuple(x for x in dataf.rx2('gear') if x > 3))
        dataf_filter = dataf.filter('gear > 3')        
        self.assertEqual(ngear_gt_3, dataf_filter.nrow)

    def testFilter_OneFilter_Function(self):
        dataf = dplyr.DataFrame(mtcars)
        ngear_gt_3 = len(tuple(x for x in dataf.rx2('gear') if x > 3))
        dataf_filter = dplyr.filter(dataf, 'gear > 3')        
        self.assertEqual(ngear_gt_3, dataf_filter.nrow)

    def testSplitMergeFunction(self):
        dataf = dplyr.DataFrame(mtcars)
        dataf_by_gear = dataf.group_by('gear')
        dataf_sum_gear = dataf_by_gear.summarize(foo='sum(gear)')
        self.assertEquals(type(dataf_sum_gear), dplyr.DataFrame)
    
    def testJoin(self):
        dataf_a = dplyr.DataFrame(mtcars)
        dataf_b = dataf_a.mutate(foo=1)
        dataf_c = dataf_a.inner_join(dataf_b)
        all_names = list(dataf_a.colnames)
        all_names.append('foo')
        try:
            # Python 3
            self.assertCountEqual(all_names, dataf_c.colnames)
        except AttributeError as ae:
            # Python 2.7
            self.assertItemsEqual(all_names, dataf_c.colnames)

    def testCollect(self):
        dataf = dplyr.DataFrame(mtcars)
        dataf_collected = dataf.collect()
        # FIXME: no real test here. Just ensuring that it is returning
        #        without error
        self.assertEquals(dplyr.DataFrame, type(dataf_collected))
        
    def testCollect(self):
        dataf = dplyr.DataFrame(mtcars)
        dataf_collected = dataf.collect()
        # FIXME: no real test here. Just ensuring that it is returning
        #        without error
        self.assertEquals(dplyr.DataFrame, type(dataf_collected))

        
def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(DplyrTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
