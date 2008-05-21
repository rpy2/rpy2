import unittest
import rpy2.rinterface as rinterface

try:
    #FIXME: can starting and stopping an embedded R be done several times ?
    rinterface.initEmbeddedR()
except:
    pass


class EmbeddedRTestCase(unittest.TestCase):
    def testSetWriteConsole(self):
        buf = ""
        def f(x, buf=buf):
            buf = buf + x

        rinterface.setWriteConsole(f)
        code = rinterface.SexpVector(["1+2", ], rinterface.STRSXP)
        rinterface.baseNameSpaceEnv["eval"](code)
        self.assertEquals("[1] 3", buf)

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(EmbeddedRTestCase)
    return suite

if __name__ == '__main__':
     unittest.main()
