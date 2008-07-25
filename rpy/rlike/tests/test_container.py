import unittest
import itertools
import rpy2.rlike.container as rlc

class ArgsDictTestCase(unittest.TestCase):

    def testNew(self):
        nl = rlc.ArgsDict()

        x = (('a', 123), ('b', 456), ('c', 789))
        nl = rlc.ArgsDict(x)

    def testLen(self):
        x = rlc.ArgsDict()
        self.assertEquals(0, len(x))

        x['a'] = 2
        x['b'] = 1

        self.assertEquals(2, len(x))

    def testGetSetitem(self):
        x = rlc.ArgsDict()
        
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
        x = rlc.ArgsDict()
        
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
        x = rlc.ArgsDict()
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

        args = (('a', 5), ('b', 4), ('c', 3),
                ('d', 2), ('e', 1))
        x = rlc.ArgsDict(args)
        k = f(**x)
        for ki, ko in itertools.izip(args, k):
            self.assertEquals(ki[0], ko)

    def testItems(self):

        args = (('a', 5), ('b', 4), ('c', 3),
                ('d', 2), ('e', 1))
        x = rlc.ArgsDict(args)
        it = x.items()
        for ki, ko in itertools.izip(args, it):
            self.assertEquals(ki[0], ko[0])
            self.assertEquals(ki[1], ko[1])

    
def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(ArgsDictTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
