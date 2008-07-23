import unittest
import itertools
import rpy2.rlike.container as rlc

class NamedListTestCase(unittest.TestCase):

    def testNew(self):
        nl = rlc.NamedList()

        x = (('a', 123), ('b', 456), ('c', 789))
        nl = rlc.NamedList(x)

    def testLen(self):
        x = rlc.NamedList()
        self.assertEquals(0, len(x))

        x['a'] = 2
        x['b'] = 1

        self.assertEquals(2, len(x))

    def testGetSetitem(self):
        x = rlc.NamedList()
        
        x['a'] = 1
        self.assertEquals(1, len(x))
        self.assertEquals(1, x['a'])
        self.assertEquals(0, x.index('a'))
        x['a'] = 2
        self.assertEquals(1, len(x))
        self.assertEquals(2, x['a'])
        self.assertEquals(0, x.index('a'))
        x['b'] = 1
        self.assertEquals(2, len(x))
        self.assertEquals(1, x['b'])
        self.assertEquals(1, x.index('b'))
        
    def testGetSetitemWithNone(self):
        x = rlc.NamedList()
        
        x['a'] = 1
        x[None] = 2
        self.assertEquals(2, len(x))
        x['b'] = 5
        self.assertEquals(3, len(x))
        self.assertEquals(1, x['a'])
        self.assertEquals(5, x['b'])
        self.assertEquals(0, x.index('a'))
        self.assertEquals(2, x.index('b'))
        
    def testReverse(self):
        x = rlc.NamedList()
        x['a'] = 3
        x['b'] = 2
        x['c'] = 1
        x.reverse()
        self.assertEquals(1, x['c'])
        self.assertEquals(0, x.index('c'))
        self.assertEquals(2, x['b'])
        self.assertEquals(1, x.index('b'))
        self.assertEquals(3, x['a'])
        self.assertEquals(2, x.index('a'))
        
    def testCall(self):

        def f(**kwargs):
            return [k for k in kwargs]
                
        x = rlc.NamedList()
        x['a'] = 3
        x['b'] = 2
        x['c'] = 1
        
        k = f(**x)
        for ki, ko in itertools.izip(x, k):
            self.assertTrue(ki, ko)

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(NamedListTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
