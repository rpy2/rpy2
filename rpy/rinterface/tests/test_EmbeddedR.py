import unittest
import itertools
import rpy2.rinterface as rinterface
import sys, os, tempfile

rinterface.initr()

def onlyAQUAorWindows(function):
    def res(self):
        platform = rinterface.baseNameSpaceEnv.get('.Platform')
        platform_gui = [e for i, e in enumerate(platform.do_slot('names')) if e == 'GUI'][0]
        platform_ostype = [e for i, e in enumerate(platform.do_slot('names')) if e == 'OS.type'][0]
        if (platform_gui != 'AQUA') and (platform_ostype != 'windows'):
            self.assertTrue(False) # cannot be tested outside GUI==AQUA or OS.type==windows
            return None
        else:
            return function(self)


class EmbeddedRTestCase(unittest.TestCase):

    def tearDown(self):
        rinterface.setWriteConsole(rinterface.consolePrint)
        rinterface.setReadConsole(rinterface.consoleRead)
        rinterface.setReadConsole(rinterface.consoleFlush)

    def testSetWriteConsole(self):
        buf = []
        def f(x):
            buf.append(x)

        rinterface.setWriteConsole(f)
        self.assertEquals(rinterface.getWriteConsole(), f)
        code = rinterface.SexpVector(["3", ], rinterface.STRSXP)
        rinterface.baseNameSpaceEnv["print"](code)
        self.assertEquals('[1] "3"\n', str.join('', buf))

    def testWriteConsoleWithError(self):
        def f(x):
            raise Exception("Doesn't work.")
        rinterface.setWriteConsole(f)

        tmp_file = tempfile.NamedTemporaryFile()
        stderr = sys.stderr
        sys.stderr = tmp_file
        try:
            code = rinterface.SexpVector(["3", ], rinterface.STRSXP)
            rinterface.baseNameSpaceEnv["print"](code)
        except Exception, e:
            sys.stderr = stderr
            raise e
        sys.stderr = stderr
        tmp_file.seek(0)
        errorstring = ''.join(tmp_file.readlines())
        self.assertTrue(errorstring.startswith('Traceback'))
        tmp_file.close()

    @onlyAQUAorWindows
    def testSetFlushConsole(self):
        flush = {'count': 0}
        def f():
            flush['count'] = flush['count'] + 1
            
        rinterface.setFlushConsole(f)
        self.assertEquals(rinterface.getFlushConsole(), f)
        rinterface.baseNameSpaceEnv.get("flush.console")()
        self.assertEquals(1, flush['count'])
        rinterface.setWriteConsole(rinterface.consoleFlush)

    @onlyAQUAorWindows
    def testFlushConsoleWithError(self):
        def f(prompt):
            raise Exception("Doesn't work.")
        rinterface.setFlushConsole(f)

        tmp_file = tempfile.NamedTemporaryFile()
        stderr = sys.stderr
        sys.stderr = tmp_file
        try:
            res = rinterface.baseNameSpaceEnv.get("flush.console")()
        except Exception, e:
            sys.stderr = stderr
            raise e
        sys.stderr = stderr
        tmp_file.seek(0)
        errorstring = ''.join(tmp_file.readlines())
        self.assertTrue(errorstring.startswith('Traceback'))
        tmp_file.close()

    def testSetReadConsole(self):
        yes = "yes\n"
        def sayyes(prompt):
            return yes
        rinterface.setReadConsole(sayyes)
        self.assertEquals(rinterface.getReadConsole(), sayyes)
        res = rinterface.baseNameSpaceEnv["readline"]()
        self.assertEquals(yes.strip(), res[0])
        rinterface.setReadConsole(rinterface.consoleRead)

    def testReadConsoleWithError(self):
        def f(prompt):
            raise Exception("Doesn't work.")
        rinterface.setReadConsole(f)

        tmp_file = tempfile.NamedTemporaryFile()

        stderr = sys.stderr
        sys.stderr = tmp_file
        try:
            res = rinterface.baseNameSpaceEnv["readline"]()
        except Exception, e:
            sys.stderr = stderr
            raise e
        sys.stderr = stderr
        tmp_file.seek(0)
        errorstring = ''.join(tmp_file.readlines())
        self.assertTrue(errorstring.startswith('Traceback'))
        tmp_file.close()
        
#FIXME: end and initialize again causes currently a lot a trouble...
    def testCallErrorWhenEndedR(self):
        self.assertTrue(False) # worked when tested, but calling endEmbeddedR causes trouble
        t = rinterface.baseNameSpaceEnv['date']
        rinterface.endr(1)
        self.assertRaises(RuntimeError, t)
        rinterface.initr()

    def testStr_typeint(self):
        t = rinterface.baseNameSpaceEnv['letters']
        self.assertEquals('STRSXP', rinterface.str_typeint(t.typeof))
        t = rinterface.baseNameSpaceEnv['pi']
        self.assertEquals('REALSXP', rinterface.str_typeint(t.typeof))

    def testStr_typeint_invalid(self):
        self.assertRaises(LookupError, rinterface.str_typeint, 99)

    def testGet_initoptions(self):
        options = rinterface.get_initoptions()
        self.assertEquals(len(rinterface.initoptions),
                          len(options))
        for o1, o2 in itertools.izip(rinterface.initoptions, options):
            self.assertEquals(o1, o2)
        
    def testSet_initoptions(self):
        self.assertRaises(RuntimeError, rinterface.set_initoptions, 
                          ('aa', '--verbose', '--no-save'))

class ObjectDispatchTestCase(unittest.TestCase):
    def testObjectDispatchLang(self):
        formula = rinterface.globalEnv.get('formula')
        obj = formula(rinterface.StrSexpVector(['y ~ x', ]))
        self.assertTrue(isinstance(obj, rinterface.SexpVector))
        self.assertEquals(rinterface.LANGSXP, obj.typeof)

    def testObjectDispatchVector(self):
        letters = rinterface.globalEnv.get('letters')
        self.assertTrue(isinstance(letters, rinterface.SexpVector))

    def testObjectDispatchClosure(self):
        #import pdb; pdb.set_trace()
        help = rinterface.globalEnv.get('sum')
        self.assertTrue(isinstance(help, rinterface.SexpClosure))

def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(EmbeddedRTestCase)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ObjectDispatchTestCase))
    return suite

if __name__ == '__main__':
     unittest.main()
