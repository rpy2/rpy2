import unittest
import rpy2.rinterface as rinterface

try:
    #FIXME: can starting and stopping an embedded R be done several times ?
    rinterface.initEmbeddedR()
except:
    pass


class EmbeddedRTestCase(unittest.TestCase):
    def testSetWriteConsole(self):
        buf = []
        def f(x):
            buf.append(x)

        rinterface.setWriteConsole(f)
        code = rinterface.SexpVector(["3", ], rinterface.STRSXP)
        rinterface.baseNameSpaceEnv["print"](code)
        self.assertEquals('[1] "3"\n', str.join('', buf))
        rinterface.setWriteConsole(rinterface.consolePrint)



def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(EmbeddedRTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
