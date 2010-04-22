import unittest
import itertools
import pickle
import rpy2.rinterface as rinterface
import sys, os, subprocess, time, tempfile, signal

rinterface.initr()




def onlyAQUAorWindows(function):
    def res(self):
        platform = rinterface.baseenv.get('.Platform')
        platform_gui = [e for i, e in enumerate(platform.do_slot('names')) if e == 'GUI'][0]
        platform_ostype = [e for i, e in enumerate(platform.do_slot('names')) if e == 'OS.type'][0]
        if (platform_gui != 'AQUA') and (platform_ostype != 'windows'):
            self.assertTrue(False) # cannot be tested outside GUI==AQUA or OS.type==windows
            return None
        else:
            return function(self)

class CustomException(Exception):
    pass

class EmbeddedRTestCase(unittest.TestCase):


    def testConsolePrint(self):
        tmp_file = tempfile.NamedTemporaryFile()
        stdout = sys.stdout
        sys.stdout = tmp_file
        try:
            rinterface.consolePrint('haha')
        except Exception, e:
            sys.stdout = stdout
            raise e
        sys.stdout = stdout
        tmp_file.flush()
        tmp_file.seek(0)
        self.assertEquals('haha', ''.join(tmp_file.readlines()))
        tmp_file.close()


    def testCallErrorWhenEndedR(self):
        if sys.version_info[0] == 2 and sys.version_info[1] < 6:
            self.assertTrue(False) # cannot be tested with Python < 2.6
            return None
        import multiprocessing
        def foo(queue):
            import rpy2.rinterface as rinterface
            rdate = rinterface.baseenv['date']
            rinterface.endr(1)
            try:
                tmp = rdate()
                res = (False, None)
            except RuntimeError, re:
                res = (True, re)
            except Exception, e:
                res = (False, e)
            queue.put(res)
        q = multiprocessing.Queue()
        p = multiprocessing.Process(target = foo, args = (q,))
        p.start()
        res = q.get()
        p.join()
        self.assertTrue(res[0])

    def testStr_typeint(self):
        t = rinterface.baseenv['letters']
        self.assertEquals('STRSXP', rinterface.str_typeint(t.typeof))
        t = rinterface.baseenv['pi']
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

    def testInterruptR(self):
        if sys.version_info[0] == 2 and sys.version_info[1] < 6:
            self.assertTrue(False) # Test unit currently requires Python >= 2.6
        rpy_code = tempfile.NamedTemporaryFile(mode = 'w', suffix = '.py',
                                               delete = False)
        rpy_code_str = """
import sys
import rpy2.robjects as ro
def f(x):
  pass
ro.rinterface.set_writeconsole(f)
rcode = "i <- 0; "
rcode += "while(TRUE) { "
rcode += "i <- i+1; "
rcode += "Sys.sleep(0.01); "
rcode += "}"
try:
  ro.r(rcode)
except Exception, e:
  sys.exit(0)
  """

        rpy_code.write(rpy_code_str)
        rpy_code.close()
        child_proc = subprocess.Popen(('python', rpy_code.name))
        time.sleep(1)  # required for the SIGINT to function
        # (appears like a bug w/ subprocess)
        # (the exact sleep time migth be machine dependent :( )
        child_proc.send_signal(signal.SIGINT)
        time.sleep(1)  # required for the SIGINT to function
        ret_code = child_proc.poll()
        self.assertFalse(ret_code is None) # Interruption failed


class CallbacksTestCase(unittest.TestCase):
    def tearDown(self):
        rinterface.set_writeconsole(rinterface.consolePrint)
        rinterface.set_readconsole(rinterface.consoleRead)
        rinterface.set_readconsole(rinterface.consoleFlush)
        rinterface.set_choosefile(rinterface.chooseFile)

    def testSetWriteConsole(self):
        buf = []
        def f(x):
            buf.append(x)

        rinterface.set_writeconsole(f)
        self.assertEquals(rinterface.get_writeconsole(), f)
        code = rinterface.SexpVector(["3", ], rinterface.STRSXP)
        rinterface.baseenv["print"](code)
        self.assertEquals('[1] "3"\n', str.join('', buf))

    def testWriteConsoleWithError(self):
        def f(x):
            raise CustomException("Doesn't work.")
        rinterface.set_writeconsole(f)

        tmp_file = tempfile.NamedTemporaryFile()
        stderr = sys.stderr
        sys.stderr = tmp_file
        try:
            code = rinterface.SexpVector(["3", ], rinterface.STRSXP)
            rinterface.baseenv["print"](code)
        except Exception, e:
            sys.stderr = stderr
            raise e
        sys.stderr = stderr
        tmp_file.flush()
        tmp_file.seek(0)
        errorstring = ''.join(tmp_file.readlines())
        self.assertTrue(errorstring.startswith('Traceback'))
        tmp_file.close()

    @onlyAQUAorWindows
    def testSetFlushConsole(self):
        flush = {'count': 0}
        def f():
            flush['count'] = flush['count'] + 1

        rinterface.set_flushconsole(f)
        self.assertEquals(rinterface.get_flushconsole(), f)
        rinterface.baseenv.get("flush.console")()
        self.assertEquals(1, flush['count'])
        rinterface.set_writeconsole(rinterface.consoleFlush)

    @onlyAQUAorWindows
    def testFlushConsoleWithError(self):
        def f(prompt):
            raise Exception("Doesn't work.")
        rinterface.set_flushconsole(f)

        tmp_file = tempfile.NamedTemporaryFile()
        stderr = sys.stderr
        sys.stderr = tmp_file
        try:
            res = rinterface.baseenv.get("flush.console")()
        except Exception, e:
            sys.stderr = stderr
            raise e
        sys.stderr = stderr
        tmp_file.flush()
        tmp_file.seek(0)
        errorstring = ''.join(tmp_file.readlines())
        self.assertTrue(errorstring.startswith('Traceback'))
        tmp_file.close()

    def testSetReadConsole(self):
        yes = "yes\n"
        def sayyes(prompt):
            return yes
        rinterface.set_readconsole(sayyes)
        self.assertEquals(rinterface.get_readconsole(), sayyes)
        res = rinterface.baseenv["readline"]()
        self.assertEquals(yes.strip(), res[0])
        rinterface.set_readconsole(rinterface.consoleRead)

    def testReadConsoleWithError(self):
        def f(prompt):
            raise Exception("Doesn't work.")
        rinterface.set_readconsole(f)

        tmp_file = tempfile.NamedTemporaryFile()

        stderr = sys.stderr
        sys.stderr = tmp_file
        try:
            res = rinterface.baseenv["readline"]()
        except Exception, e:
            sys.stderr = stderr
            raise e
        sys.stderr = stderr
        tmp_file.flush()
        tmp_file.seek(0)
        errorstring = ''.join(tmp_file.readlines())
        self.assertTrue(errorstring.startswith('Traceback'))
        tmp_file.close()
        
    def testSetShowMessage(self):
        def f(message):
            return "foo"
        rinterface.set_showmessage(f)
        #FIXME: incomplete test

    def testShowMessageWithError(self):
        def f(prompt):
            raise Exception("Doesn't work.")
        rinterface.set_showmessage(f)
        #FIXME: incomplete test

    def testSetChooseFile(self):
        me = "me"
        def chooseMe(prompt):
            return me
        rinterface.set_choosefile(chooseMe)
        self.assertEquals(rinterface.get_choosefile(), chooseMe)
        res = rinterface.baseenv["file.choose"]()
        self.assertEquals(me, res[0])
        rinterface.set_choosefile(rinterface.chooseFile)

    def testChooseFileWithError(self):
        def noconsole(x):
            pass
        rinterface.set_writeconsole(noconsole) # reverted by the tearDown method
        def f(prompt):
            raise Exception("Doesn't work.")
        rinterface.set_choosefile(f)

        tmp_file = tempfile.NamedTemporaryFile()
        stderr = sys.stderr
        sys.stderr = tmp_file
        try:
            res = rinterface.baseenv["file.choose"]()
        except rinterface.RRuntimeError, rre:
            pass
        except Exception, e:
            sys.stderr = stderr
            raise e
        sys.stderr = stderr
        tmp_file.flush()
        tmp_file.seek(0)
        errorstring = ''.join(tmp_file.readlines())
        self.assertTrue(errorstring.startswith('Traceback'))
        tmp_file.close()

    def testSetShowFiles(self):
        sf = []
        def f(fileheaders, wtitle, fdel, pager):
            sf.append(wtitle)
            for tf in fileheaders:
                sf.append(tf)

        rinterface.set_showfiles(f)
        file_path = rinterface.baseenv["file.path"]
        r_home = rinterface.baseenv["R.home"]
        filename = file_path(r_home(rinterface.StrSexpVector(("doc", ))), 
                             rinterface.StrSexpVector(("COPYRIGHTS", )))
        res = rinterface.baseenv["file.show"](filename)
        self.assertEquals(filename[0], sf[1][1])
        self.assertEquals('R Information', sf[0])

    def testShowFilesWithError(self):
        def f(fileheaders, wtitle, fdel, pager):
            raise Exception("Doesn't work")

        rinterface.set_showfiles(f)
        file_path = rinterface.baseenv["file.path"]
        r_home = rinterface.baseenv["R.home"]
        filename = file_path(r_home(rinterface.StrSexpVector(("doc", ))), 
                             rinterface.StrSexpVector(("COPYRIGHTS", )))

        tmp_file = tempfile.NamedTemporaryFile()
        stderr = sys.stderr
        sys.stderr = tmp_file
        try:
            res = rinterface.baseenv["file.show"](filename)
        except rinterface.RRuntimeError, rre:
            pass
        except Exception, e:
            sys.stderr = stderr
            raise e
        sys.stderr = stderr
        tmp_file.flush()
        tmp_file.seek(0)
        errorstring = ''.join(tmp_file.readlines())
        self.assertTrue(errorstring.startswith('Traceback'))
        tmp_file.close()

    def testSetCleanUp(self):
        orig_cleanup = rinterface.get_cleanup()
        def f(saveact, status, runlast):
            return False
        rinterface.set_cleanup(f)
        rinterface.set_cleanup(orig_cleanup)

    def testCleanUp(self):
        orig_cleanup = rinterface.get_cleanup()
        def f(saveact, status, runlast):
            return None
        r_quit = rinterface.baseenv['q']
        rinterface.set_cleanup(f)        
        self.assertRaises(rinterface.RRuntimeError, r_quit)
        rinterface.set_cleanup(orig_cleanup)


class ObjectDispatchTestCase(unittest.TestCase):
    def testObjectDispatchLang(self):
        formula = rinterface.globalenv.get('formula')
        obj = formula(rinterface.StrSexpVector(['y ~ x', ]))
        self.assertTrue(isinstance(obj, rinterface.SexpVector))
        self.assertEquals(rinterface.LANGSXP, obj.typeof)

    def testObjectDispatchVector(self):
        letters = rinterface.globalenv.get('letters')
        self.assertTrue(isinstance(letters, rinterface.SexpVector))

    def testObjectDispatchClosure(self):
        #import pdb; pdb.set_trace()
        help = rinterface.globalenv.get('sum')
        self.assertTrue(isinstance(help, rinterface.SexpClosure))

    def testObjectDispatchRawVector(self):
        raw = rinterface.baseenv.get('raw')
        rawvec = raw(rinterface.IntSexpVector((10, )))
        self.assertEquals(rinterface.RAWSXP, rawvec.typeof)

class SerializeTestCase(unittest.TestCase):
    def testUnserialize(self):
        x = rinterface.IntSexpVector([1,2,3])
        x_serialized = x.__getstate__()
        x_again = rinterface.unserialize(x_serialized, x.typeof)
        identical = rinterface.baseenv["identical"]
        self.assertFalse(x.rsame(x_again))
        self.assertTrue(identical(x, x_again)[0])

    def testPickle(self):
        x = rinterface.IntSexpVector([1,2,3])
        f = tempfile.NamedTemporaryFile()
        pickle.dump(x, f)
        f.flush()
        f.seek(0)
        x_again = pickle.load(f)
        f.close()
        identical = rinterface.baseenv["identical"]
        self.assertTrue(identical(x, x_again)[0])
                     
def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(EmbeddedRTestCase)
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(CallbacksTestCase))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ObjectDispatchTestCase))
    return suite

if __name__ == '__main__':
    tr = unittest.TextTestRunner(verbosity = 2)
    tr.run(suite())
    
