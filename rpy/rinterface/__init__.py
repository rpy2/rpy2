import os
import sys
import warnings
import subprocess

if ((sys.version_info[0] == 2 and sys.version_info[1] < 7) or
        (sys.version_info[0] == 3 and sys.version_info[1] < 3)):
    raise RuntimeError(
        "Python (>=2.7 and < 3.0) or >=3.3 are required to run rpy2")


class RRuntimeWarning(RuntimeWarning):
    pass


def _r_home_from_subprocess():
    """Return the R home directory from calling 'R RHOME'."""
    try:
        tmp = subprocess.check_output(("R", "RHOME"), universal_newlines=True)
    except Exception as exc:  # FileNotFoundError, WindowsError, etc
        return
    r_home = tmp.split(os.linesep)
    if r_home[0].startswith("WARNING"):
        r_home = r_home[1]
    else:
        r_home = r_home[0].strip()
    return r_home


def _r_home_from_registry():
    """Return the R home directory from the Windows Registry."""
    try:
        import winreg
    except ImportError:
        import _winreg as winreg
    try:
        hkey = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE,
                                "Software\\R-core\\R",
                                0, winreg.KEY_QUERY_VALUE)
        r_home = winreg.QueryValueEx(hkey, "InstallPath")[0]
        winreg.CloseKey(hkey)
    except Exception as exc:  # FileNotFoundError, WindowsError, etc
        return
    if sys.version_info[0] == 2:
        r_home = r_home.encode(sys.getfilesystemencoding())
    return r_home


def _load_r_dll(r_home):
    """Load the R.DLL matching Python's bitness.

    Add directories containing R DLLs to the PATH environment variable.

    """
    import ctypes
    r_arch = ('i386', 'x64')[sys.maxsize > 2**32]
    r_mod = os.path.join(r_home, 'modules', r_arch)
    r_bin = os.path.join(r_home, 'bin', r_arch)
    r_dll = os.path.join(r_bin, 'R.dll')
    if not os.path.exists(r_dll):
        raise RuntimeError("Unable to locate R.dll at %s" % r_dll)
    if r_bin not in os.environ.get('PATH'):
        os.environ['PATH'] = ';'.join((os.environ.get('PATH'), r_bin, r_mod))
    ctypes.CDLL(r_dll)


R_HOME = os.environ.get("R_HOME")

if not R_HOME:
    R_HOME = _r_home_from_subprocess()

if not R_HOME and sys.platform == 'win32':
    R_HOME = _r_home_from_registry()

if not R_HOME:
    raise RuntimeError("""The R home directory could not be determined.

    Try to install R <https://www.r-project.org/>,
    set the R_HOME environment variable to the R home directory, or
    add the directory of the R interpreter to the PATH environment variable.
    """)

if not os.environ.get("R_HOME"):
    os.environ['R_HOME'] = R_HOME

if sys.platform == 'win32':
    _load_r_dll(R_HOME)

# cleanup the namespace
del(os)

from rpy2.rinterface._rinterface import (baseenv,
                                         emptyenv,
                                         endr,
                                         initr,
                                         get_choosefile,
                                         get_cleanup,
                                         get_flushconsole,
                                         get_initoptions,
                                         get_readconsole,
                                         get_resetconsole,
                                         get_showfiles,
                                         get_showmessage,
                                         get_writeconsole_regular,
                                         get_writeconsole_warnerror,
                                         globalenv,
                                         initoptions,
                                         parse,
                                         process_revents,
                                         protected_rids,
                                         python_type_tag,
                                         set_choosefile,
                                         set_cleanup,
                                         set_flushconsole,
                                         set_initoptions,
                                         set_readconsole,
                                         set_resetconsole,
                                         set_showfiles,
                                         set_showmessage,
                                         set_writeconsole_regular,
                                         set_writeconsole_warnerror,
                                         str_typeint,
                                         BoolSexpVector,
                                         ByteSexpVector,
                                         ComplexSexpVector,
                                         CPLXSXP,
                                         CLOSXP,
                                         ENVSXP,
                                         EXPRSXP,
                                         EXTPTRSXP,
                                         FALSE,
                                         FloatSexpVector,
                                         IntSexpVector,
                                         INTSXP,
                                         ListSexpVector,
                                         LANGSXP,
                                         LGLSXP,
                                         MissingArg,
                                         NACharacterType,
                                         NAComplexType,
                                         NAIntegerType,
                                         NALogicalType,
                                         NARealType,
                                         NA_Character,
                                         NA_Complex,
                                         NA_Integer,
                                         NA_Logical,
                                         NA_Real,
                                         NULL,
                                         REALSXP,
                                         R_LEN_T_MAX,
                                         R_VERSION_BUILD,
                                         R_NilValue,
                                         RNULLType,
                                         RParsingError,
                                         RParsingIncompleteError,
                                         RRuntimeError,
                                         Sexp,
                                         SexpClosure,
                                         SexpEnvironment,
                                         SexpExtPtr,
                                         SexpSymbol,
                                         SexpS4,
                                         SexpVector,
                                         StrSexpVector,
                                         STRSXP,
                                         SYMSXP,
                                         TRUE,
                                         VECSXP)

# wrapper in case someone changes sys.stdout:
if sys.version_info.major == 3:
    # Print became a regular function in Python 3, making
    # the workaround (mostly) unnecessary (python2to3 still needs it
    # wrapped in a function
    def consolePrint(x):
        print(x)
else:
    def consolePrint(x):
        sys.stdout.write(x)

set_writeconsole_regular(consolePrint)

def consoleWarn(x):
    warnings.warn(x, RRuntimeWarning)
set_writeconsole_warnerror(consoleWarn)

def consoleFlush():
    sys.stdout.flush()

set_flushconsole(consoleFlush)

# wrapper in case someone changes sys.stdout:
if sys.version_info.major == 3:
    # 'raw_input()' became 'input()' in Python 3
    def consoleRead(prompt):
        text = input(prompt)
        text += "\n"
        return text
else:
    def consoleRead(prompt):
        text = raw_input(prompt)
        text += "\n"
        return text

set_readconsole(consoleRead)


def consoleMessage(x):
    sys.stdout.write(x)

set_showmessage(consoleMessage)


def chooseFile(prompt):
    res = raw_input(prompt)
    return res
set_choosefile(chooseFile)

def showFiles(wtitle, titlefiles, rdel, pager):
    sys.stdout.write(titlefiles)

    for wt in wtitle:
        sys.stdout.write(wt[0])
        f = open(wt[1])
        for row in f:
            sys.stdout.write(row)
        f.close()
    return 0
set_showfiles(showFiles)

def rternalize(function):
    """ Takes an arbitrary Python function and wrap it
    in such a way that it can be called from the R side. """
    assert callable(function) #FIXME: move the test down to C
    rpy_fun = SexpExtPtr(function, tag = python_type_tag)
    #rpy_type = ri.StrSexpVector(('.Python', ))
    #FIXME: this is a hack. Find a better way.
    template = parse('function(...) { .External(".Python", foo, ...) }')
    template[0][2][1][2] = rpy_fun
    return baseenv['eval'](template)

# def cleanUp(saveact, status, runlast):
#     return True

# setCleanUp(cleanUp)
