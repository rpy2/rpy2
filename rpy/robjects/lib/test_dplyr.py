import unittest
from rpy2.robjects.vectors import IntVector, DataFrame
from rpy2.robjects.lib import dplyr

class DplyrTestCase(unittest.TestCase):

    def testFunction_inner_join(self):
        dataf_a = DataFrame({'x': IntVector((1,2))})
        dataf_b = DataFrame({'x': IntVector((2,5,1))})
        dataf_ab = dplyr.inner_join(dataf_a, dataf_b, by="x")
        self.assertEqual(2, dataf_ab.nrow)

    def testMethod_inner_join(self):
        DataFrame = dplyr.DataFrame
        dataf_a = DataFrame({'x': IntVector((1,2))})
        dataf_b = DataFrame({'x': IntVector((2,5,1))})
        dataf_ab = dataf_a.inner_join(dataf_b, by="x")
        self.assertEqual(2, dataf_ab.nrow)

    def testFunction_filter(self):
        DataFrame = dplyr.DataFrame
        dataf_a = DataFrame({'x': IntVector((1,2,3))})
        dataf_af = dplyr.filter(dataf_a, 'x < 2')
        self.assertEqual(1, dataf_af.nrow)

    def testMethodfilter(self):
        DataFrame = dplyr.DataFrame
        dataf_a = DataFrame({'x': IntVector((1,2,3))})
        dataf_af = dataf_a.filter('x < 2')
        self.assertEqual(1, dataf_af.nrow)

    def testFunction_group_by_summarize_arrange(self):
        dataf_a = DataFrame({'x': IntVector((1,2,1)),
                             'y': IntVector((3,4,5))})
        dataf_ag = dplyr.group_by(dataf_a, 'x')
        dataf_as = dplyr.summarize(dataf_ag, count='n()')
        dataf_aa = dplyr.arrange(dataf_as, 'count')
        self.assertEqual(2, dataf_aa.nrow)
        self.assertSequenceEqual([1, 2], dataf_aa.rx2('count'))

    def testMethod_group_by_summarize_arrange(self):
        DataFrame = dplyr.DataFrame
        dataf_a = DataFrame({'x': IntVector((1,2,1)),
                             'y': IntVector((3,4,5))})
        dataf_ag = dataf_a.group_by('x')
        dataf_as = dataf_ag.summarize(count='n()')
        dataf_aa = dataf_as.arrange('count')
        self.assertEqual(2, dataf_aa.nrow)
        self.assertSequenceEqual([1, 2], dataf_aa.rx2('count'))

    def testFunction_mutate(self):
        DataFrame = dplyr.DataFrame
        dataf_a = DataFrame({'x': IntVector((1,2))})
        dataf_am = dplyr.mutate(dataf_a, y='x + 3')
        self.assertEqual(2, dataf_am.ncol)
        self.assertSequenceEqual([x+3 for x in dataf_a.rx2('x')],
                                 dataf_am.rx2('y'))

    def testMethod_mutate(self):
        DataFrame = dplyr.DataFrame
        dataf_a = DataFrame({'x': IntVector((1,2))})
        dataf_am = dataf_a.mutate(y='x + 3')
        self.assertEqual(2, dataf_am.ncol)
        self.assertSequenceEqual([x+3 for x in dataf_a.rx2('x')],
                                 dataf_am.rx2('y'))

    def testFunction_select(self):
        dataf_a = DataFrame({'x': IntVector((1,2)),
                             'y': IntVector((3,4))})
        dataf_as = dplyr.select(dataf_a, 'y')
        self.assertEqual(1, dataf_as.ncol)
        dataf_as = dplyr.select(dataf_a, '-x')
        self.assertEqual(1, dataf_as.ncol)

    def testMethod_select(self):
        DataFrame = dplyr.DataFrame
        dataf_a = DataFrame({'x': IntVector((1,2)),
                             'y': IntVector((3,4))})
        dataf_as = dataf_a.select('y')
        self.assertEqual(1, dataf_as.ncol)
        dataf_as = dataf_a.select('-x')
        self.assertEqual(1, dataf_as.ncol)


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(DplyrTestCase)

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
