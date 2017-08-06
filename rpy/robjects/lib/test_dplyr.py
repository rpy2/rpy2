import unittest
import uuid

from rpy2.robjects.lib import dplyr
from rpy2.robjects.packages import importr
from rpy2.robjects.vectors import IntVector
from rpy2 import robjects

_quiet_require = robjects.r('function(x) suppressMessages(substitute(require(x)))')
    
missing_rpacks = tuple(rpack for rpack in ('RSQLite', 'dbplyr') if not _quiet_require(rpack)[0])

class DataFrameTestCase(unittest.TestCase):

    DataFrame = dplyr.DataFrame
    
    def testFunction_inner_join(self):
        dataf_a = self.DataFrame({'x': IntVector((1,2))})
        dataf_b = self.DataFrame({'x': IntVector((2,5,1))})
        dataf_ab = dplyr.inner_join(dataf_a, dataf_b, by="x")
        self.assertEqual(2, dataf_ab.collect().nrow)

    def testMethod_inner_join(self):
        self.DataFrame = self.DataFrame
        dataf_a = self.DataFrame({'x': IntVector((1,2))})
        dataf_b = self.DataFrame({'x': IntVector((2,5,1))})
        dataf_ab = dataf_a.inner_join(dataf_b, by="x")
        self.assertEqual(2, dataf_ab.collect().nrow)

    def testFunction_filter(self):
        self.DataFrame = self.DataFrame
        dataf_a = self.DataFrame({'x': IntVector((1,2,3))})
        dataf_af = dplyr.filter(dataf_a, 'x < 2')
        self.assertEqual(1, dataf_af.collect().nrow)

    def testMethodfilter(self):
        self.DataFrame = self.DataFrame
        dataf_a = self.DataFrame({'x': IntVector((1,2,3))})
        dataf_af = dataf_a.filter('x < 2')
        self.assertEqual(1, dataf_af.collect().
                         nrow)

    def testFunction_group_by_summarize_arrange(self):
        dataf_a = self.DataFrame({'x': IntVector((1,2,1)),
                                  'y': IntVector((3,4,5))})
        dataf_ag = dplyr.group_by(dataf_a, 'x')
        dataf_as = dplyr.summarize(dataf_ag, count='n()')
        dataf_aa = dplyr.arrange(dataf_as, 'count')
        self.assertEqual(2, dataf_aa.collect().nrow)
        self.assertSequenceEqual([1, 2], dataf_aa.collect().rx2('count'))

    def testMethod_group_by_summarize_arrange(self):
        self.DataFrame = self.DataFrame
        dataf_a = self.DataFrame({'x': IntVector((1,2,1)),
                                  'y': IntVector((3,4,5))})
        dataf_ag = dataf_a.group_by('x')
        dataf_as = dataf_ag.summarize(count='n()')
        dataf_aa = dataf_as.arrange('count')
        self.assertEqual(2, dataf_aa.collect().nrow)
        self.assertSequenceEqual([1, 2], dataf_aa.collect().rx2('count'))

    def testFunction_mutate(self):
        self.DataFrame = self.DataFrame
        dataf_a = self.DataFrame({'x': IntVector((1,2))})
        dataf_am = dplyr.mutate(dataf_a, y='x + 3')
        self.assertEqual(2, dataf_am.collect().ncol)
        self.assertSequenceEqual([x+3 for x in dataf_a.collect().rx2('x')],
                                 dataf_am.collect().rx2('y'))

    def testMethod_mutate(self):
        self.DataFrame = self.DataFrame
        dataf_a = self.DataFrame({'x': IntVector((1,2))})
        dataf_am = dataf_a.mutate(y='x + 3')
        self.assertEqual(2, dataf_am.ncol)
        self.assertSequenceEqual([x+3 for x in dataf_a.collect().rx2('x')],
                                 dataf_am.collect().rx2('y'))

    def testFunction_select(self):
        dataf_a = self.DataFrame({'x': IntVector((1,2)),
                                  'y': IntVector((3,4))})
        dataf_as = dplyr.select(dataf_a, 'y')
        self.assertEqual(1, dataf_as.collect().ncol)
        dataf_as = dplyr.select(dataf_a, '-x')
        self.assertEqual(1, dataf_as.collect().ncol)

    def testMethod_select(self):
        self.DataFrame = self.DataFrame
        dataf_a = self.DataFrame({'x': IntVector((1,2)),
                                  'y': IntVector((3,4))})
        dataf_as = dataf_a.select('y')
        self.assertEqual(1, dataf_as.collect().ncol)
        dataf_as = dataf_a.select('-x')
        self.assertEqual(1, dataf_as.collect().ncol)



@unittest.skipUnless(len(missing_rpacks) == 0,
                     'The R package(s) %s is/are missing' % ', '.join(missing_rpacks))
class SQLiteTestCase(DataFrameTestCase):

    RSQLite = importr('RSQLite')
    DBI = importr('DBI')

    def DataFrame(self, *args, **kwargs):
        dataf = dplyr.DataFrame(*args, **kwargs)
        res = dplyr.copy_to(self.dbcon, dataf, name=str(uuid.uuid4()))
        print(res)
        return res
        
    def setUp(self):
        self.dbcon = self.DBI.dbConnect(self.RSQLite.SQLite(), ":memory:")

    def tearDown(self):
        self.DBI.dbDisconnect(self.dbcon)

        
def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(DataFrameTestCase)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(SQLiteTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
