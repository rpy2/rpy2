import logging
import warnings
from . import _rinterface_capi as _rinterface

logger = logging.getLogger(__name__)

READCONSOLE_SIGNATURE = 'int(char *, unsigned char *, int, int)'
WRITECONSOLE_SIGNATURE = 'void(char *, int)'
WRITECONSOLE_EX_SIGNATURE = 'void(char *, int, int)'
SHOWMESSAGE_SIGNATURE = 'void(char *)'
CHOOSEFILE_SIGNATURE = 'int(int, char *, int)'
CLEANUP_SIGNATURE = 'void(SA_TYPE, int, int)'
SHOWFILE_SIGNATURE = ('int(int, const char **, const char **, '
                      '    const char *, Rboolean, const char *)')


def logged_exceptions(func, logger=logger):
    def _(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(str(e))
    return _


@logged_exceptions
def consoleread(prompt):
    return input(prompt)


@_rinterface.ffi.callback(READCONSOLE_SIGNATURE)
def _consoleread(prompt, buf, n, addtohistory):
    try:
        reply = consoleread(_rinterface._cchar_to_str(prompt))
        # TODO: handle non-ASCII encodings
        reply_b = reply.encode('ASCII')
        reply_n = min(n, len(reply_b))
        _rinterface.ffi.memmove(buf,
                                reply_b,
                                reply_n)
        if reply_n < n:
            buf[reply_n] = ord(b'\n')
        for i in range(reply_n+1, n):
            buf[i] = 0        
        if reply_n == 0:
            success = 0
        else:
            success = 1
    except Exception as e:
        # TODO: fix error handling
        success = 0
        print(e)
    return success


@logged_exceptions
def consolewrite_print(s):
    # TODO: is the callback for flush working with Linux ?
    print(s, end='', flush=True)


@logged_exceptions
def consolewrite_warnerror(s):
    # TODO: use an rpy2/R-specific warning instead of UserWarning.
    warnings.warn(s)


@_rinterface.ffi.callback(WRITECONSOLE_EX_SIGNATURE)
def _consolewrite_ex(buf, n, otype):
    s = _rinterface._cchar_to_str_with_maxlen(buf, maxlen=n)
    try:
        if otype == 0:
            consolewrite_print(s)
        else:
            consolewrite_warnerror(s)
    except Exception as e:
        print(e)


@logged_exceptions
def showmessage(s):
    print('R wants to show a message')
    print(s)


@_rinterface.ffi.callback(SHOWMESSAGE_SIGNATURE)
def _showmessage(buf):
    s = _rinterface._cchar_to_str(buf)
    showmessage(s)


@logged_exceptions
def choosefile(new):
    return input('Enter file name:')
    

@_rinterface.ffi.callback(CHOOSEFILE_SIGNATURE)
def _choosefile(new, buf, n):
    res = choosefile(new)
    if res is None:
        return 0
    res_cdata = _rinterface._str_to_cchar(res)
    _rinterface.ffi.memmove(buf, res_cdata, len(res_cdata))
    return len(res_cdata)


def showfile(s):
    print(s)


@_rinterface.ffi.callback(SHOWFILE_SIGNATURE)
def _showfile(nfiles, files, headers, wtitle, delete, pager):
    for i in range(nfiles):
        fn = files[i]
        print('File: %s' % _rinterface.ffi.string(fn))
        with open(fn) as fh:
            for row in fh:
                print(row)
        print('---')


@logged_exceptions
def cleanup(saveact, status, runlast):
    pass


@_rinterface.ffi.callback(CLEANUP_SIGNATURE)
def _cleanup(saveact, status, runlast):
     cleanup(saveact, status, runlast)
