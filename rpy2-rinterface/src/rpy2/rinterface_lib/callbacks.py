"""Callbacks available from R's C-API.

The callbacks make available in R's C-API can be specified as
Python functions, with the module providing the adapter code
that makes it possible."""

from contextlib import contextmanager
import logging
import typing
import os
from rpy2.rinterface_lib import openrlib
from rpy2.rinterface_lib import ffi_proxy
from rpy2.rinterface_lib import conversion

logger = logging.getLogger(__name__)

_CCHAR_ENCODING = 'utf-8'


# TODO: rename to "replace_in_module"
@contextmanager
def obj_in_module(module, name: str, obj: typing.Any):
    obj_orig = getattr(module, name)
    setattr(module, name, obj)
    try:
        yield
    finally:
        setattr(module, name, obj_orig)


def consoleflush():
    pass


_FLUSHCONSOLE_EXCEPTION_LOG = 'R[flush console]: %s'


@ffi_proxy.callback(ffi_proxy._consoleflush_def,
                    openrlib._rinterface_cffi)
def _consoleflush() -> None:
    try:
        with openrlib.rlock:
            consoleflush()
    except Exception as e:
        logger.error(_FLUSHCONSOLE_EXCEPTION_LOG, str(e))


def consoleread(prompt: str) -> str:
    """Read input for the R console.

    :param prompt: The message prompted.
    :return: A string with the input returned by the user.
    """
    return input(prompt)


_READCONSOLE_EXCEPTION_LOG = 'R[read into console]: %s'
_READCONSOLE_INTERNAL_EXCEPTION_LOG = ('Internal rpy2 error with '
                                       '_consoleread callback: %s')


@ffi_proxy.callback(ffi_proxy._consoleread_def,
                    openrlib._rinterface_cffi)
def _consoleread(prompt, buf, n: int, addtohistory) -> int:
    success = None
    try:
        s = conversion._cchar_to_str(prompt, _CCHAR_ENCODING)
        with openrlib.rlock:
            reply = consoleread(s)
    except Exception as e:
        success = 0
        logger.error(_READCONSOLE_EXCEPTION_LOG, str(e))
    if success == 0:
        return success

    try:
        # TODO: Should the coding be dynamically extracted from
        # elsewhere ?
        reply_b = reply.encode('utf-8')
        reply_n = min(n, len(reply_b))
        pybuf = bytearray(n)
        pybuf[:reply_n] = reply_b[:reply_n]
        pybuf[reply_n] = ord('\n')
        pybuf[reply_n+1] = 0
        openrlib.ffi.memmove(buf,
                             pybuf,
                             n)
        if reply_n == 0:
            success = 0
        else:
            success = 1
    except Exception as e:
        success = 0
        logger.error(_READCONSOLE_INTERNAL_EXCEPTION_LOG,
                     str(e))
    return success


def consolereset() -> None:
    pass


_RESETCONSOLE_EXCEPTION_LOG = 'R[reset console]: %s'


@ffi_proxy.callback(ffi_proxy._consolereset_def,
                    openrlib._rinterface_cffi)
def _consolereset() -> None:
    try:
        with openrlib.rlock:
            consolereset()
    except Exception as e:
        logger.error(_RESETCONSOLE_EXCEPTION_LOG, str(e))


def consolewrite_print(s: str) -> None:
    """R writing to the console/terminal.

    :param s: the data to write to the console/terminal.
    """
    # TODO: is the callback for flush working with Linux ?
    print(s, end='', flush=True)


def consolewrite_warnerror(s: str) -> None:
    # TODO: use an rpy2/R-specific warning instead of UserWarning.
    logger.warning(_WRITECONSOLE_EXCEPTION_LOG, s)


_WRITECONSOLE_EXCEPTION_LOG = 'R[write to console]: %s'


@ffi_proxy.callback(ffi_proxy._consolewrite_ex_def,
                    openrlib._rinterface_cffi)
def _consolewrite_ex(buf, n: int, otype: int) -> None:
    s = conversion._cchar_to_str_with_maxlen(buf, n, _CCHAR_ENCODING)
    try:
        with openrlib.rlock:
            if otype == 0:
                consolewrite_print(s)
            else:
                consolewrite_warnerror(s)
    except Exception as e:
        logger.error(_WRITECONSOLE_EXCEPTION_LOG, str(e))


def showmessage(s: str) -> None:
    print('R wants to show a message')
    print(s)


_SHOWMESSAGE_EXCEPTION_LOG = 'R[show message]: %s'


@ffi_proxy.callback(ffi_proxy._showmessage_def,
                    openrlib._rinterface_cffi)
def _showmessage(buf):
    s = conversion._cchar_to_str(buf, _CCHAR_ENCODING)
    try:
        with openrlib.rlock:
            showmessage(s)
    except Exception as e:
        logger.error(_SHOWMESSAGE_EXCEPTION_LOG, str(e))


def choosefile(new):
    return input('Enter file name:')


_CHOOSEFILE_EXCEPTION_LOG = 'R[choose file]: %s'


@ffi_proxy.callback(ffi_proxy._choosefile_def,
                    openrlib._rinterface_cffi)
def _choosefile(new, buf, n: int) -> int:
    try:
        with openrlib.rlock:
            res = choosefile(new)
    except Exception as e:
        logger.error(_CHOOSEFILE_EXCEPTION_LOG, str(e))
        res = None

    if res is None:
        return 0

    res_cdata = conversion._str_to_cchar(res)
    openrlib.ffi.memmove(buf, res_cdata, len(res_cdata))
    return len(res_cdata)


def showfiles(filenames: typing.Tuple[str, ...],
              headers: typing.Tuple[str, ...],
              wtitle: typing.Optional[str],
              pager: typing.Optional[str]) -> None:
    """R showing files.

    :param filenames: A tuple of file names.
    :param headers: A tuple of strings (TODO: check what it is)
    :wtitle: Title of the "window" showing the files.
    :pager: Pager to use to show the list of files.
    """
    for fn in filenames:
        print('File: %s' % fn)
        with open(fn) as fh:
            for row in fh:
                print(row)
            print('---')


_SHOWFILE_EXCEPTION_LOG = 'R[show file]: %s'
_SHOWFILE_INTERNAL_EXCEPTION_LOG = ('Internal rpy2 error while '
                                    'showing files for R: %s')


@ffi_proxy.callback(ffi_proxy._showfiles_def,
                    openrlib._rinterface_cffi)
def _showfiles(nfiles: int, files, headers, wtitle, delete, pager) -> int:
    filenames = []
    headers_str = []
    wtitle_str = None
    pager_str = None
    try:
        wtitle_str = conversion._cchar_to_str(wtitle, _CCHAR_ENCODING)
        pager_str = conversion._cchar_to_str(pager, _CCHAR_ENCODING)
        for i in range(nfiles):
            filenames.append(
                conversion._cchar_to_str(files[i],
                                         _CCHAR_ENCODING)
            )
            headers_str.append(
                conversion._cchar_to_str(headers[i],
                                         _CCHAR_ENCODING)
            )
    except Exception as e:
        logger.error(_SHOWFILE_INTERNAL_EXCEPTION_LOG, str(e))

    if len(filenames):
        res = 0
    else:
        res = 1
    try:
        with openrlib.rlock:
            showfiles(tuple(filenames),
                      tuple(headers_str),
                      wtitle_str,
                      pager_str)
    except Exception as e:
        res = 1
        logger.error(_SHOWFILE_EXCEPTION_LOG, str(e))

    return res


def cleanup(saveact, status, runlast):
    pass


_CLEANUP_EXCEPTION_LOG = 'R[cleanup]: %s'


@ffi_proxy.callback(ffi_proxy._cleanup_def,
                    openrlib._rinterface_cffi)
def _cleanup(saveact, status, runlast):
    try:
        with openrlib.rlock:
            cleanup(saveact, status, runlast)
    except Exception as e:
        logger.error(_CLEANUP_EXCEPTION_LOG, str(e))


def processevents() -> None:
    """Process R events.

    This function can be periodically called by R to handle
    events such as window resizing in an interactive graphical
    device."""
    pass


_PROCESSEVENTS_EXCEPTION_LOG = 'R[processevents]: %s'


@ffi_proxy.callback(ffi_proxy._processevents_def,
                    openrlib._rinterface_cffi)
def _processevents() -> None:
    try:
        with openrlib.rlock:
            processevents()
    except KeyboardInterrupt:
        # This function is a Python callback. A keyboard interruption is
        # captured in Python, but R must be notified that an interruption
        # occured so it can handle it.
        rlib = openrlib.rlib
        if os.name == 'nt':
            # On Windows, the global C-level R variable `UserBreak` is set
            # to one to notifying R that a `SIGBREAK` has been sent
            # (see the R source - `src/gnuwin32/embeddedR.c:my_onintr()`).
            rlib.UserBreak = 1
        else:
            # On UNIX-like, R can be notified that a SIGINT has been sent
            # through the C-level R variable `R_interrupts_pending`
            # (see the R source - `src/main/main.c:handleInterrupt()`)
            rlib.R_interrupts_pending = 1
    except Exception as e:
        logger.error(_PROCESSEVENTS_EXCEPTION_LOG, str(e))


def busy(x: int) -> None:
    """R is busy.

    :param x: TODO this is an integer but I do not know what it does.
    """
    pass


_BUSY_EXCEPTION_LOG = 'R[busy]: %s'


@ffi_proxy.callback(ffi_proxy._busy_def,
                    openrlib._rinterface_cffi)
def _busy(which: int) -> None:
    try:
        with openrlib.rlock:
            busy(which)
    except Exception as e:
        logger.error(_BUSY_EXCEPTION_LOG, str(e))


def callback() -> None:
    pass


_CALLBACK_EXCEPTION_LOG = 'R[callback]: %s'


@ffi_proxy.callback(ffi_proxy._callback_def,
                    openrlib._rinterface_cffi)
def _callback() -> None:
    try:
        with openrlib.rlock:
            callback()
    except Exception as e:
        logger.error(_CALLBACK_EXCEPTION_LOG, str(e))


def yesnocancel(question: str) -> int:
    """Asking a user to answer yes, no, or cancel.

    :param question: The question asked to the user
    :return: An integer with the answer.
    """
    return int(input(question))


_YESNOCANCEL_EXCEPTION_LOG = 'R[yesnocancel]: %s'


@ffi_proxy.callback(ffi_proxy._yesnocancel_def,
                    openrlib._rinterface_cffi)
def _yesnocancel(question):
    try:
        q = conversion._cchar_to_str(question, _CCHAR_ENCODING)
        with openrlib.rlock:
            res = yesnocancel(q)
    except Exception as e:
        logger.error(_YESNOCANCEL_EXCEPTION_LOG, str(e))
    return res
