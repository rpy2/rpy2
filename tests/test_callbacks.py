from contextlib import contextmanager
import pytest
import sys
import tempfile
import rpy2.rinterface_cffi as rinterface

rinterface.initr()


@contextmanager
def obj_in_module(module, name, func):
    backup_func = getattr(module, name)
    setattr(module, name, func)
    try:
        yield
    finally:
        setattr(module, name, backup_func)


def test_set_consolewrite_print():
    buf = []
    def f(x):
        buf.append(x)

    with obj_in_module(rinterface.callbacks, 'consolewrite_print', f):
        code = rinterface.StrSexpVector(["3", ])
        rinterface.baseenv["print"](code)
        assert '[1] "3"\n' == str.join('', buf)


def test_consolewrite_print_error():
    def f(x):
        raise CustomException("Doesn't work.")

    with obj_in_module(rinterface.callbacks, 'consolewrite_print', f):
        with tempfile.NamedTemporaryFile() as tmp_file:
            stderr = sys.stderr
            sys.stderr = tmp_file
            try:
                code = rinterface.StrSexpVector(["3", ])
                rinterface.baseenv["print"](code)
            except Exception as e:
                sys.stderr = stderr
                raise e
            sys.stderr = stderr
            tmp_file.flush()
            tmp_file.seek(0)
            assert "Doesn't work." == str(sys.last_value)


def testSetResetConsole():
    reset = [0]
    def f():
        reset[0] += 1

    with obj_in_module(rinterface.callbacks, 'consolereset', f):
        with pytest.raises(rinterface.RRuntimeError), \
             pytest.warns(rinterface.RRuntimeWarning):
                rinterface.baseenv['eval'](rinterface.parse('1+"a"'))
        assert reset[0] == 1

    
    @onlyAQUAorWindows
    def testSetFlushConsole(self):
        flush = {'count': 0}
        def f():
            flush['count'] = flush['count'] + 1

        with obj_in_module(rinterface.callbacks, 'consoleflush', f):
            self.assertEqual(rinterface.get_flushconsole(), f)
            rinterface.baseenv.get("flush.console")()
            self.assertEqual(1, flush['count'])
            rinterface.set_writeconsole_regular(rinterface.consoleFlush)

    @onlyAQUAorWindows
    def testFlushConsoleWithError(self):
        def f(prompt):
            raise Exception("Doesn't work.")

        with obj_in_module(rinterface.callbacks, 'consoleflush', f):
            with tempfile.NamedTemporaryFile() as tmp_file:
                stderr = sys.stderr
                sys.stderr = tmp_file
                try:
                    res = rinterface.baseenv.get('flush.console')()
                except Exception as e:
                    sys.stderr = stderr
                    raise e
                sys.stderr = stderr
                tmp_file.flush()
                tmp_file.seek(0)
                self.assertEqual("Doesn't work.", str(sys.last_value))


def test_consoleread():
    yes = 'yes\n'
    def sayyes(prompt):
        return yes
    with obj_in_module(rinterface.callbacks, 'consoleread', sayyes):
        res = rinterface.baseenv['readline']()
        assert yes.strip() == res[0]


def test_console_read_with_error():
    def f(prompt):
        raise Exception("Doesn't work.")
    with obj_in_module(rinterface.callbacks, 'consoleread', f):

        with tempfile.NamedTemporaryFile() as tmp_file:

            stderr = sys.stderr
            sys.stderr = tmp_file
            try:
                res = rinterface.baseenv['readline']()
            except Exception as e:
                sys.stderr = stderr
                raise e
            sys.stderr = stderr
            tmp_file.flush()
            tmp_file.seek(0)
            assert "Doesn't work." == str(sys.last_value)

        
def test_show_message():
    def f(message):
        return 'foo'
    with obj_in_module(rinterface.callbacks, 'showmessage', f):
        pass
    # TODO: incomplete test


def test_show_message_with_error():
    def f(prompt):
        raise Exception("Doesn't work.")
    with obj_in_module(rinterface.callbacks, 'showmessage', f):
        pass
    # TODO: incomplete test

    
def test_choosefile():
    me = "me"
    def chooseMe(prompt):
        return me
    with obj_in_module(rinterface.callbacks, 'choosefile', chooseMe):
        res = rinterface.baseenv['file.choose']()
        assert me == res[0]


def test_choosefile_error():
    def noconsole(x):
        pass
    with obj_in_module(rinterface.callbacks, 'consolewrite_print', noconsole):
        def f(prompt):
            raise Exception("Doesn't work.")
        with obj_in_module(rinterface.callbacks, 'choosefile', f):
            with pytest.raises(rinterface.RRuntimeError):
                with pytest.warns(rinterface.RRuntimeWarning):
                    rinterface.baseenv["file.choose"]()
            assert "Doesn't work." == str(sys.last_value)


@pytest.mark.skip(reason='WIP')    
def test_showfiles():
    sf = []
    def f(fileheaders, wtitle, fdel, pager):
        sf.append(wtitle)
        for tf in fileheaders:
            sf.append(tf)

    with obj_in_module(rinterface.callbacks, 'showfiles', f):
        file_path = rinterface.baseenv['file.path']
        r_home = rinterface.baseenv['R.home']
        filename = file_path(r_home(rinterface.StrSexpVector(('doc', ))), 
                             rinterface.StrSexpVector(('COPYRIGHTS', )))
        res = rinterface.baseenv['file.show'](filename)
        assert filename[0] == sf[1][1]
        assert 'R Information' == sf[0]


@pytest.mark.skip(reason='WIP')    
def test_showfiles_error():
    def f(fileheaders, wtitle, fdel, pager):
        raise Exception("Doesn't work.")

    with obj_in_module(rinterface.callbacks, 'showfiles', f):
        file_path = rinterface.baseenv['file.path']
        r_home = rinterface.baseenv['R.home']
        filename = file_path(r_home(rinterface.StrSexpVector(('doc', ))), 
                             rinterface.StrSexpVector(('COPYRIGHTS', )))

        with tempfile.NamedTemporaryFile() as tmp_file:
            stderr = sys.stderr
            sys.stderr = tmp_file
            try:
                res = rinterface.baseenv['file.show'](filename)
            except rinterface.RRuntimeError:
                pass
            except Exception as e:
                sys.stderr = stderr
                raise e
            sys.stderr = stderr
            tmp_file.flush()
            tmp_file.seek(0)
            assert "Doesn't work." == str(sys.last_value)


@pytest.mark.skip(reason='WIP')
def test_cleanup():
    def f(saveact, status, runlast):
        return None
    with obj_in_module(rinterface.callbacks, 'cleanup', f):
        r_quit = rinterface.baseenv['q']
        with pytest.raises(rinterface.RRuntimeError):
            r_quit()
