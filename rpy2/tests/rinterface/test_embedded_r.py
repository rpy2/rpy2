import gc
import multiprocessing
import os
import pickle
import pytest
from rpy2 import rinterface
import rpy2
import rpy2.rinterface_lib._rinterface_capi as _rinterface
import signal
import sys
import subprocess
import tempfile
import time


rinterface.initr()


def is_AQUA_or_Windows(function):
    platform = rinterface.baseenv.find('.Platform')
    names = platform.do_slot('names')
    platform_gui = names[names.index('GUI')]
    platform_ostype = names[names.index('OS.type')]
    if (platform_gui != 'AQUA') and (platform_ostype != 'windows'):
        return False
    else:
        return True


class CustomException(Exception):
    pass


def _call_with_ended_r(queue):
    import rpy2.rinterface_cffi as rinterface
    rinterface.initr()
    rdate = rinterface.baseenv['date']
    rinterface.endr(0)
    try:
        rdate()
        res = (False, None)
    except RuntimeError as re:
        res = (True, re)
    except Exception as e:
        res = (False, e)
    queue.put(res)


def _init_r():
    from rpy2 import rinterface
    rinterface.initr()


@pytest.mark.skip(reason='Spawned process seems to share '
                  'initialization state with parent.')
def test_call_error_when_ended_r():
    q = multiprocessing.Queue()
    ctx = multiprocessing.get_context('spawn')
    p = ctx.Process(target=_call_with_ended_r, args=(q,))
    p.start()
    res = q.get()
    p.join()
    assert res[0]


# TODO: is this test still making sense ?
def test_get_initoptions():
    options = rinterface.embedded.get_initoptions()
    assert len(rinterface.embedded._options) == len(options)
    for o1, o2 in zip(rinterface.embedded._options, options):
        assert o1 == o2


def test_set_initoptions_after_init():
    with pytest.raises(RuntimeError):
        rinterface.embedded.set_initoptions(('aa', '--verbose',
                                             '--no-save'))


def test_initr():
    preserve_hash = True
    args = ()
    if os.name != 'nt':
        args = (preserve_hash,)
    proc = multiprocessing.Process(target=_init_r,
                                   args=args)
    proc.start()
    proc.join()


def test_parse_ok():
    xp = rinterface.parse('2 + 3')
    assert xp.typeof == rinterface.RTYPES.EXPRSXP
    assert 2.0 == xp[0][1][0]
    assert 3.0 == xp[0][2][0]


def test_parse_unicode():
    xp = rinterface.parse(u'"\u21a7"')
    assert len(xp) == 1
    assert len(xp[0]) == 1


def test_parse_incomplete_error():
    with pytest.raises(_rinterface.RParsingError) as rpe:
        rinterface.parse("2 + 3 /")
    assert rpe.value.status == (_rinterface
                                .PARSING_STATUS.PARSE_INCOMPLETE)


def test_parse_error():
    with pytest.raises(_rinterface.RParsingError):
        rinterface.parse("2 + 3 , 1")


def test_parse_error_when_evaluting():
    with pytest.raises(_rinterface.RParsingError):
        rinterface.parse("list(''=1)")


def test_parse_invalid_string():
    with pytest.raises(TypeError):
        rinterface.parse(3)


def test_rternalize():
    def f(x, y):
        return x[0]+y[0]
    rfun = rinterface.rternalize(f)
    res = rfun(1, 2)
    assert res[0] == 3


def test_rternalize_return_sexp():
    def f(x, y):
        return rinterface.IntSexpVector([x[0], y[0]])
    rfun = rinterface.rternalize(f)
    res = rfun(1, 2)
    assert tuple(res) == (1, 2)


def test_rternalize_namedargs():
    def f(x, y, z=None):
        if z is None:
            return x[0]+y[0]
        else:
            return z[0]
    rfun = rinterface.rternalize(f)
    res = rfun(1, 2)
    assert res[0] == 3
    res = rfun(1, 2, z=8)
    assert res[0] == 8


def test_external_python():
    def f(x):
        return 3

    rpy_fun = rinterface.SexpExtPtr.from_pyobject(f)
    _python = rinterface.StrSexpVector(('.Python', ))
    res = rinterface.baseenv['.External'](_python,
                                          rpy_fun, 1)
    assert len(res) == 1
    assert res[0] == 3


# TODO: what is this ?
def testExternalPythonFromExpression():
    xp_name = rinterface.StrSexpVector(('expression',))
    xp = rinterface.baseenv['vector'](xp_name, 3)


def testInterruptR():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py',
                                     delete=False) as rpy_code:
        rpy2_path = os.path.dirname(rpy2.__path__[0])

        rpy_code_str = """
        import sys
        sys.path.insert(0, '%s')
        import rpy2.rinterface as ri

        ri.initr()
        def f(x):
            pass
        ri.set_writeconsole_regular(f)
        rcode = \"\"\"
        i <- 0;
        while(TRUE) {
          i <- i+1;
          Sys.sleep(0.01);
        }\"\"\"
        try:
            ri.baseenv['eval'](ri.parse(rcode))
        except Exception as e:
            sys.exit(0)
      """ % rpy2_path

        rpy_code.write(rpy_code_str)
    cmd = (sys.executable, rpy_code.name)
    with open(os.devnull, 'w') as fnull:
        creationflags = 0
        if os.name == 'nt':
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
        child_proc = subprocess.Popen(cmd,
                                      stdout=fnull,
                                      stderr=fnull,
                                      creationflags=creationflags)
        time.sleep(1)  # required for the SIGINT to function
        # (appears like a bug w/ subprocess)
        # (the exact sleep time migth be machine dependent :( )
        sigint = signal.CTRL_C_EVENT if os.name == 'nt' else signal.SIGINT
        child_proc.send_signal(sigint)
        time.sleep(1)  # required for the SIGINT to function
        ret_code = child_proc.poll()
    assert ret_code is not None  # Interruption failed


# TODO: still needed ?
def test_rpy_memory():
    x = rinterface.IntSexpVector(range(10))
    x_rid = x.rid
    assert x_rid in set(z[0] for z in rinterface._rinterface.protected_rids())
    del(x)
    # TODO: Why calling collect() twice ?
    gc.collect()
    gc.collect()
    s = set(z[0] for z in rinterface._rinterface.protected_rids())
    assert x_rid not in s


def test_object_dispatch_lang():
    formula = rinterface.globalenv.find('formula')
    obj = formula(rinterface.StrSexpVector(['y ~ x', ]))
    assert isinstance(obj, rinterface.SexpVector)
    assert obj.typeof == rinterface.RTYPES.LANGSXP


def test_object_dispatch_vector():
    robj = rinterface.globalenv.find('letters')
    assert isinstance(robj, rinterface.SexpVector)


def test_object_dispatch_closure():
    robj = rinterface.globalenv.find('sum')
    assert isinstance(robj, rinterface.SexpClosure)


def test_object_dispatch_rawvector():
    rawfunc = rinterface.baseenv.find('raw')
    rawvec = rawfunc(rinterface.IntSexpVector((10, )))
    assert rinterface.RTYPES.RAWSXP == rawvec.typeof


def test_unserialize():
    x = rinterface.IntSexpVector([1, 2, 3])
    x_serialized = x.__getstate__()
    x_again = rinterface.Sexp(
        rinterface.unserialize(x_serialized))
    identical = rinterface.baseenv['identical']
    assert not x.rsame(x_again)
    assert identical(x, x_again)[0]


def test_pickle():
    x = rinterface.IntSexpVector([1, 2, 3])
    with tempfile.NamedTemporaryFile() as f:
        pickle.dump(x, f)
        f.flush()
        f.seek(0)
        x_again = pickle.load(f)
    identical = rinterface.baseenv['identical']
    assert identical(x, x_again)[0]
