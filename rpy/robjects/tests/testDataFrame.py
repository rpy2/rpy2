import unittest
import rpy2.robjects as robjects
rinterface = robjects.rinterface
import rpy2.rlike.container as rlc

import array
import csv, tempfile

class DataFrameTestCase(unittest.TestCase):

    def testNewFromTaggedList(self):
        letters = robjects.r.letters        
        numbers = robjects.r('1:26')
        df = robjects.DataFrame(rlc.TaggedList((letters, numbers),
                                               tags = ('letters', 'numbers')))

        self.assertEquals("data.frame", df.rclass[0])

    def testNewFromRObject(self):
        numbers = robjects.r('1:5')
        self.assertRaises(ValueError, robjects.DataFrame, numbers)

        rlist = robjects.r('list(a=1, b=2, c=3)')
        self.assertRaises(ValueError, robjects.DataFrame, rlist)

        rdataf = robjects.r('data.frame(a=1:2, b=c("a", "b"))')
        dataf = robjects.DataFrame(rdataf)        

    def testNewFromOrdDict(self):
        od = rlc.OrdDict(c=(('a', robjects.IntVector((1,2))),
                            ('b', robjects.StrVector(('c', 'd')))
                            ))
        dataf = robjects.DataFrame(od)
        self.assertEquals(1, dataf.rx2('a')[0])
        
    def testDim(self):
        letters = robjects.r.letters        
        numbers = robjects.r('1:26')
        df = robjects.DataFrame(rlc.TaggedList((letters, numbers),
                                               tags = ('letters', 'numbers')))
        self.assertEquals(26, df.nrow)
        self.assertEquals(2, df.ncol)

    def testFrom_csvfile(self):
        column_names = ('letter', 'value')
        data = (column_names,
                ('a', 1),
                ('b', 2),
                ('c', 3))
        fh = tempfile.NamedTemporaryFile(mode = "w", delete = False)
        csv_w = csv.writer(fh)
        csv_w.writerows(data)
        fh.close()
        dataf = robjects.DataFrame.from_csvfile(fh.name)
        self.assertEquals(column_names, tuple(dataf.names))
        self.assertEquals(3, dataf.nrow)
        self.assertEquals(2, dataf.ncol)

    def testTo_csvfile(self):
        fh = tempfile.NamedTemporaryFile(mode = "w", delete = False)
        fh.close()
        d = {'letter': robjects.StrVector('abc'),
             'value' : robjects.IntVector((1, 2, 3))}
        dataf = robjects.DataFrame(d)
        dataf.to_csvfile(fh.name)
        dataf = robjects.DataFrame.from_csvfile(fh.name)
        self.assertEquals(3, dataf.nrow)
        self.assertEquals(2+1, dataf.ncol) # row names means +1

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(DataFrameTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
