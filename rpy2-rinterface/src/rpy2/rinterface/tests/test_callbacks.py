from . import utils
import builtins
import io
import logging
import os
import pytest
import tempfile
import sys
import rpy2.rinterface as rinterface
from rpy2.rinterface_lib import callbacks
from rpy2.rinterface_lib import openrlib

rinterface.initr()


def test_consolewrite_print():
    tmp_file = io.StringIO()
    stdout = sys.stdout
    sys.stdout = tmp_file
    try:
        callbacks.consolewrite_print('haha')
    finally:
        sys.stdout = stdout
    tmp_file.flush()
    tmp_file.seek(0)
    assert 'haha' == ''.join(s for s in tmp_file).rstrip()
    tmp_file.close()


def test_set_consolewrite_print():

    def make_callback():
        buf = []

        def f(x):
            nonlocal buf
            buf.append(x)
        return f

    f = make_callback()
    with utils.obj_in_module(callbacks, 'consolewrite_print', f):
        code = rinterface.StrSexpVector(["3", ])
        rinterface.baseenv["print"](code)
        buf = f.__closure__[0].cell_contents
        assert '[1] "3"\n' == ''.join(buf)


def test_consolewrite_print_error(caplog):

    msg = "Doesn't work."

    def f(x):
        raise Exception(msg)

    with utils.obj_in_module(callbacks, 'consolewrite_print', f),\
            caplog.at_level(logging.ERROR, logger='callbacks.logger'):
        code = rinterface.StrSexpVector(["3", ])
        caplog.clear()
        rinterface.baseenv["print"](code)
        assert len(caplog.record_tuples) > 0
        for x in caplog.record_tuples:
            assert x == ('rpy2.rinterface_lib.callbacks',
                         logging.ERROR,
                         (callbacks
                          ._WRITECONSOLE_EXCEPTION_LOG % msg))


def testSetResetConsole():

    def make_callback():
        reset = 0

        def f():
            nonlocal reset
            reset += 1
        return f

    f = make_callback()

    with utils.obj_in_module(callbacks, 'consolereset', f):
        callbacks._consolereset()
        assert f.__closure__[0].cell_contents == 1


def test_resetconsole_error(caplog):
    error_msg = "Doesn't work."

    def f():
        raise Exception(error_msg)

    with utils.obj_in_module(callbacks, 'consolereset', f),\
            caplog.at_level(logging.ERROR, logger='callbacks.logger'):
        caplog.clear()
        callbacks._consolereset()
        assert len(caplog.record_tuples) > 0
        for x in caplog.record_tuples:
            assert x == ('rpy2.rinterface_lib.callbacks',
                         logging.ERROR,
                         (callbacks
                          ._RESETCONSOLE_EXCEPTION_LOG % error_msg))


@pytest.mark.skipif(os.name == 'nt', reason='Not supported on Windows')
def test_flushconsole():

    def make_callback():
        count = 0

        def f():
            nonlocal count
            count += 1
        return f

    f = make_callback()

    with utils.obj_in_module(callbacks, 'consoleflush', f):
        assert f.__closure__[0].cell_contents == 0
        rinterface.globalenv.find('flush.console')()
        assert f.__closure__[0].cell_contents == 1


@pytest.mark.skipif(os.name == 'nt', reason='Not supported on Windows')
def test_flushconsole_with_error(caplog):
    msg = "Doesn't work."

    def f():
        raise Exception(msg)

    with utils.obj_in_module(callbacks, 'consoleflush', f),\
            caplog.at_level(logging.ERROR, logger='callbacks.logger'):
        caplog.clear()
        rinterface.globalenv.find('flush.console')()
        assert len(caplog.record_tuples) > 0
        for x in caplog.record_tuples:
            assert x == ('rpy2.rinterface_lib.callbacks',
                         logging.ERROR,
                         (callbacks
                          ._FLUSHCONSOLE_EXCEPTION_LOG % msg))


def test_consoleread():
    msg_orig = 'yes'

    def sayyes(prompt):
        return msg_orig

    with utils.obj_in_module(callbacks, 'consoleread', sayyes):
        prompt = openrlib.ffi.new('char []', b'foo')
        n = 1000
        buf = openrlib.ffi.new('char [%i]' % n)
        res = callbacks._consoleread(prompt, buf, n, 0)
    assert res == 1
    msg = openrlib.ffi.string(buf).decode('utf-8')
    assert msg_orig == msg.rstrip()


def test_consoleread_empty():

    def sayyes(prompt):
        return ''

    with utils.obj_in_module(callbacks, 'consoleread', sayyes):
        prompt = openrlib.ffi.new('char []', b'foo')
        n = 1000
        buf = openrlib.ffi.new('char [%i]' % n)
        res = callbacks._consoleread(prompt, buf, n, 0)
    assert res == 0
    msg = openrlib.ffi.string(buf).decode('utf-8')
    assert msg.rstrip() == ''


def test_console_read_with_error(caplog):

    msg = "Doesn't work."

    def f(prompt):
        raise Exception(msg)

    with utils.obj_in_module(callbacks, 'consoleread', f),\
            caplog.at_level(logging.ERROR, logger='callbacks.logger'):
        caplog.clear()
        prompt = openrlib.ffi.new('char []', b'foo')
        n = 1000
        buf = openrlib.ffi.new('char [%i]' % n)
        res = callbacks._consoleread(prompt, buf, n, 0)
        assert res == 0
        assert len(caplog.record_tuples) > 0
        for x in caplog.record_tuples:
            assert x == ('rpy2.rinterface_lib.callbacks',
                         logging.ERROR,
                         (callbacks
                          ._READCONSOLE_EXCEPTION_LOG % msg))


def test_showmessage_default(capsys):
    buf = 'foo'
    callbacks.showmessage(buf)
    captured = capsys.readouterr()
    assert captured.out.split('\n')[1] == buf

    
def test_show_message():

    def make_callback():
        count = 0

        def f(message):
            nonlocal count
            count += 1

        return f

    f = make_callback()

    with utils.obj_in_module(callbacks, 'showmessage', f):
        assert f.__closure__[0].cell_contents == 0
        msg = openrlib.ffi.new('char []', b'foo')
        callbacks._showmessage(msg)
        assert f.__closure__[0].cell_contents == 1


def test_show_message_with_error(caplog):
    error_msg = "Doesn't work."

    def f(message):
        raise Exception(error_msg)

    with utils.obj_in_module(callbacks, 'showmessage', f),\
            caplog.at_level(logging.ERROR, logger='callbacks.logger'):
        caplog.clear()
        msg = openrlib.ffi.new('char []', b'foo')
        callbacks._showmessage(msg)
        assert len(caplog.record_tuples) > 0
        for x in caplog.record_tuples:
            assert x == ('rpy2.rinterface_lib.callbacks',
                         logging.ERROR,
                         (callbacks
                          ._SHOWMESSAGE_EXCEPTION_LOG % error_msg))


def test_choosefile_default():
    inputvalue = 'foo'
    with utils.obj_in_module(builtins, 'input', lambda x: inputvalue):
        assert callbacks.choosefile('foo') == inputvalue


@pytest.mark.skipif(os.name == 'nt', reason='Not supported on Windows')
def test_choosefile():
    me = "me"

    def chooseMe(new):
        return me

    with utils.obj_in_module(callbacks, 'choosefile', chooseMe):
        res = rinterface.baseenv['file.choose']()
        assert me == res[0]


@pytest.mark.skipif(os.name == 'nt', reason='Not supported on Windows')
def test_choosefile_error():

    def f(prompt):
        raise Exception("Doesn't work.")

    with utils.obj_in_module(callbacks, 'consolewrite_print',
                             utils.noconsole):
        with utils.obj_in_module(callbacks, 'choosefile', f):
            with pytest.raises(rinterface.embedded.RRuntimeError):
                rinterface.baseenv["file.choose"]()


def test_showfiles_default(capsys):
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b'abc')
        tmp.close()
        filenames = (tmp, )
        headers = ('', )
        wtitle = ''
        pager = ''
        captured = capsys.readouterr()
        callbacks.showfiles(tuple(x.name for x in filenames),
                            headers, wtitle, pager)
        captured.out.endswith('---')
        os.unlink(tmp.name)


@pytest.mark.skipif(os.name == 'nt', reason='Not supported on Windows')
def test_showfiles():
    sf = []

    def f(filenames, headers, wtitle, pager):
        sf.append(wtitle)
        for tf in filenames:
            sf.append(tf)

    with utils.obj_in_module(callbacks, 'showfiles', f):
        file_path = rinterface.baseenv['file.path']
        r_home = rinterface.baseenv['R.home']
        filename = file_path(r_home(rinterface.StrSexpVector(('doc', ))),
                             rinterface.StrSexpVector(('COPYRIGHTS', )))
        rinterface.baseenv['file.show'](filename)
        assert filename[0] == sf[1]
        assert 'R Information' == sf[0]


@pytest.mark.skipif(os.name == 'nt', reason='Not supported on Windows')
def test_showfiles_error(caplog):

    msg = "Doesn't work."

    def f(filenames, headers, wtitle, pager):
        raise Exception(msg)

    with utils.obj_in_module(callbacks, 'showfiles', f),\
            caplog.at_level(logging.ERROR, logger='callbacks.logger'):

        file_path = rinterface.baseenv['file.path']
        r_home = rinterface.baseenv['R.home']
        filename = file_path(r_home(rinterface.StrSexpVector(('doc', ))),
                             rinterface.StrSexpVector(('COPYRIGHTS', )))

        caplog.clear()
        rinterface.baseenv['file.show'](filename)

        assert len(caplog.record_tuples) > 0
        for x in caplog.record_tuples:
            assert x == ('rpy2.rinterface_lib.callbacks',
                         logging.ERROR,
                         (callbacks
                          ._SHOWFILE_EXCEPTION_LOG % msg))


@pytest.mark.skip(reason='WIP (should be run from worker process).')
def test_cleanup():

    def f(saveact, status, runlast):
        return None

    with utils.obj_in_module(callbacks, 'cleanup', f):
        r_quit = rinterface.baseenv['q']
        with pytest.raises(rinterface.embedded.RRuntimeError):
            r_quit()


def test_busy():

    busylist = []
    def busy(which):
        busylist.append(which)

    with utils.obj_in_module(callbacks, 'busy', busy):
        which = 1
        callbacks._busy(which)
    assert tuple(busylist) == (1,)


def test_callback():

    callbacklist = []
    def callback():
        callbacklist.append(1)

    with utils.obj_in_module(callbacks, 'callback', callback):
        callbacks._callback()
    assert tuple(callbacklist) == (1,)


def test_yesnocancel():

    def yesnocancel(question):
        return 1

    question = openrlib.ffi.new('char []', b'What ?')
    with utils.obj_in_module(callbacks, 'yesnocancel', yesnocancel):
        res = callbacks._yesnocancel(question)
    assert res == 1
