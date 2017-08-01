import unittest
from rpy2.robjects.vectors import IntVector, DataFrame
from rpy2.robjects.lib import dplyr

class DplyrTestCase(unittest.TestCase):

    def testInnerJoin(self):
        dataf_a = DataFrame({'x': IntVector((1,2))})
        dataf_b = DataFrame({'x': IntVector((2,5,1))})
        dataf_ab = dplyr.inner_join(dataf_a, dataf_b, by="x")
        self.assertEqual(2, dataf_ab.nrow)

    # def testFilter(self):
    #     dataf_a = DataFrame({'x': IntVector((1,2,3))}),
    #     dataf_af = dplyr.filter(dataf_a, 'x < 2')
    #     self.assertEqual(2, dataf_af.row)

    def testMutate(self):
        dataf_a = DataFrame({'x': IntVector((1,2))})
        dataf_am = dplyr.mutate(dataf_a, y='x + 3')
        self.assertEqual(2, dataf_am.ncol)
        self.assertSequenceEqual([x+3 for x in dataf_a.rx2('x')],
                                 dataf_am.rx2('y'))

    def testSelect(self):
        dataf_a = DataFrame({'x': IntVector((1,2)),
                             'y': IntVector((3,4))})
        dataf_as = dplyr.select(dataf_a, 'y')
        self.assertEqual(1, dataf_as.ncol)
        dataf_as = dplyr.select(dataf_a, '-x')
        self.assertEqual(1, dataf_as.ncol)


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(DplyrTestCase)

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
