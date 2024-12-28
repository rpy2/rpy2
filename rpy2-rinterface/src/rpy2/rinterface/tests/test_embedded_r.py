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
import textwrap
import time

SKIP_KNOWN_ISSUES = True

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


@pytest.mark.skipif(
    SKIP_KNOWN_ISSUES,
    reason=('Spawned process seems to share '
            'initialization state with parent.')
)
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


@pytest.mark.skipif(
    SKIP_KNOWN_ISSUES,
    reason=(
        'This might fail with a segfault when multithreading is involved. '
        'The underlying R C code has an unfortunate non-local jump when this '
        'parsing error is encountered.'
    )
)
def test_parse_error_when_evaluating():
    with pytest.raises(_rinterface.RParsingError):
        rinterface.parse("list(''=1)")


def test_parse_invalid_string():
    with pytest.raises(TypeError):
        rinterface.parse(3)


@pytest.mark.parametrize(
    'envir',
    (None, rinterface.globalenv, rinterface.ListSexpVector([])))
def test_evalr(envir):
    res = rinterface.evalr('1 + 2', envir=envir)
    assert tuple(res) == (3, )


@pytest.mark.parametrize(
    'envir',
    (None, rinterface.globalenv)
)
@pytest.mark.parametrize(
    'expr,visibility',
    (('x <- 1', False), ('1', True))
)
def test_evalr_expr_with_visible(envir, expr, visibility):
    value, vis = rinterface.evalr_expr_with_visible(
        rinterface.parse(expr),
        envir=envir)
    assert vis[0] == visibility


def test_rternalize_decorator():
    @rinterface.rternalize
    def rfun(x, y):
        return x[0]+y[0]
    res = rfun(1, 2)
    assert res[0] == 3


def test_rternalize_decorator_signature():
    @rinterface.rternalize(signature=True)
    def rfun(x, y):
        return x[0]+y[0]
    res = rfun(1, 2)
    assert res[0] == 3


@pytest.mark.parametrize('signature', ((True, ), (False, )))
def test_rternalize(signature):
    def f(x, y):
        return x[0]+y[0]
    rfun = rinterface.rternalize(f, signature=signature)
    res = rfun(1, 2)
    assert res[0] == 3


def test_rternalize_return_sexp():
    def f(x, y):
        return rinterface.IntSexpVector([x[0], y[0]])
    rfun = rinterface.rternalize(f, signature=False)
    res = rfun(1, 2)
    assert tuple(res) == (1, 2)


def test_rternalize_namedargs():
    def f(x, y, z=None):
        if z is None:
            return x[0]+y[0]
        else:
            return z[0]
    rfun = rinterface.rternalize(f, signature=False)
    res = rfun(1, 2)
    assert res[0] == 3
    res = rfun(1, 2, z=8)
    assert res[0] == 8


@pytest.mark.parametrize('signature', ((True, ), (False, )))
def test_rternalize_extraargs(signature):
    def f():
        return 1
    rfun = rinterface.rternalize(f, signature=signature)
    assert rfun()[0] == 1
    with pytest.raises(rinterface.embedded.RRuntimeError,
                       match=r'unused argument \(1\)'):
        rfun(1)


@pytest.mark.parametrize(
    'args',
    ((),
     (1,),
     (1, 2))
)
def test_rternalize_map_ellipsis_args(args):
    def f(x, *args):
        return len(args)
    rfun = rinterface.rternalize(f, signature=True)
    assert ('x', '...') == tuple(rinterface.baseenv['formals'](rfun).names)
    assert rfun(0, *args)[0] == len(args)


@pytest.mark.parametrize(
    'kwargs',
    ({},
     {'y': 1},
     {'y': 1, 'z': 2})
)
def test_rternalize_map_ellipsis_kwargs(kwargs):
    def f(x, **kwargs):
        return len(kwargs)
    rfun = rinterface.rternalize(f, signature=True)
    assert ('x', '...') == tuple(rinterface.baseenv['formals'](rfun).names)
    assert rfun(0, **kwargs)[0] == len(kwargs)


def test_rternalize_map_ellipsis_args_kwargs_error():
    def f(x, *args, y = 2, **kwargs):
        pass
    with pytest.raises(ValueError):
        rfun = rinterface.rternalize(f, signature=True)


def test_rternalize_formals():
    def f(a, /, b, c=1, *, d=2, e):
        return 1
    rfun = rinterface.rternalize(f, signature=True)
    rnames = rinterface.baseenv['names']
    rformals = rinterface.baseenv['formals']
    rpaste = rinterface.baseenv['paste']
    assert list(rnames(rformals(rfun))) == ['a', 'b', 'c', 'd', 'e']


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


@pytest.mark.parametrize(
    'rcode',
    ('while(TRUE) {}',
     """
     i <- 0;
     while(TRUE) {
       i <- i+1;
       Sys.sleep(0.01);
     }
     """)
)
def test_interrupt_r(rcode):
    expected_code = 42  # this is an arbitrary exit code that we check for below
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py',
                                     delete=False) as rpy_code:
        rpy2_path = os.path.dirname(rpy2.__path__[0])

        rpy_code_str = textwrap.dedent("""
        import sys
        sys.path.insert(0, '%s')
        import rpy2.rinterface as ri
        from rpy2.rinterface_lib import callbacks
        from rpy2.rinterface_lib import embedded

        ri.initr()
        def f(x):
            # This flush is important to make sure we avoid a deadlock.
            print(x, flush=True)
        rcode = '''
        message('executing-rcode')
        console.flush()
        %s
        '''
        with callbacks.obj_in_module(callbacks, 'consolewrite_print', f):
            try:
                ri.baseenv['eval'](ri.parse(rcode))
            except embedded.RRuntimeError:
                sys.exit(%d)
      """) % (rpy2_path, rcode, expected_code)

        rpy_code.write(rpy_code_str)
    cmd = (sys.executable, rpy_code.name)
    with open(os.devnull, 'w') as fnull:
        creationflags = 0
        if os.name == 'nt':
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
        # This context manager ensures that appropriate cleanup happens for the
        # process and for stdout.
        with subprocess.Popen(cmd,
                              # Since we are reading from stdout, it's important to ensure we work
                              # well with buffering. We make sure to flush when printing, but a viable
                              # alternative is starting the Python process as unbuffered using `-u`.
                              # If we weren't explicitly flushing then buffering could result in a
                              # deadlock where the parent waits for the message from the child, but the
                              # child is in an infinite loop that will only terminate if interrupted by
                              # the parent.
                              stdout=subprocess.PIPE,
                              stderr=fnull,
                              creationflags=creationflags) as child_proc:
            # We wait for the child process to send a message signalling that
            # R code is being executed since we want to ensure that we only send
            # the signal at that point. If we send it while Python is executing,
            # we would instead get a KeyboardInterrupt.
            for line in child_proc.stdout:
                if line == b'executing-rcode\n':
                    break
            sigint = signal.CTRL_C_EVENT if os.name == 'nt' else signal.SIGINT
            child_proc.send_signal(sigint)
            # Wait for the process to terminate. Timeout ensures we don't wait indefinitely.
            ret_code = child_proc.wait(timeout=10)
    # This test checks for a specific exit code to ensure that the above code
    # block exited correctly. This is important to distinguish our expected
    # process interruption from other errors the test might encounter.
    assert ret_code == expected_code


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
