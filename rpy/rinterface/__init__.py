import os, sys

try:
    R_HOME = (os.environ["R_HOME"], )
except KeyError:
    tmp = os.popen("R RHOME")
    R_HOME = tmp.readlines()
    tmp.close()
    del(tmp)

if len(R_HOME) == 0:
    if sys.platform == 'win32':
        try:
            import win32api
            import win32con
            hkey = win32api.RegOpenKeyEx(win32con.HKEY_LOCAL_MACHINE,
                                         "Software\\R-core\\R",
                                         0, win32con.KEY_QUERY_VALUE )
            R_HOME = win32api.RegQueryValueEx(hkey, "InstallPath")[0]
            win32api.RegCloseKey( hkey )
        except ImportError, ie:
            raise RuntimeError(
                "No environment variable R_HOME could be found, "
                "calling the command 'R RHOME' does not return anything, " +\
                "and unable to import win32api or win32con, " +\
                    "both of which being needed to retrieve where is R "+\
                    "from the registry. You should either specify R_HOME " +\
                    "or install the win32 package.")
        except:
            raise RuntimeError(
                "No environment variable R_HOME could be found, "
                "calling the command 'R RHOME' does not return anything, " +\
                "and unable to determine R version from the registery." +\
                    "This might be because R.exe is nowhere in your Path.")
    else:
        raise RuntimeError(
            "R_HOME not defined, and no R command in the PATH."
            )
else:
#Twist if 'R RHOME' spits out a warning
    if R_HOME[0].startswith("WARNING"):
        R_HOME = R_HOME[1]
    else:
        R_HOME = R_HOME[0]
        R_HOME = R_HOME.strip()

os.environ['R_HOME'] = R_HOME

# Win32-specific code copied from RPy-1.x
if sys.platform == 'win32':
    import win32api
    os.environ['PATH'] += ';' + os.path.join(R_HOME, 'bin')
    os.environ['PATH'] += ';' + os.path.join(R_HOME, 'modules')
    os.environ['PATH'] += ';' + os.path.join(R_HOME, 'lib')

    # Load the R dll using the explicit path
    # First try the bin dir:
    Rlib = os.path.join(R_HOME, 'bin', 'R.dll')
    # Then the lib dir:
    if not os.path.exists(Rlib):
        Rlib = os.path.join(R_HOME, 'lib', 'R.dll')
    # Otherwise fail out!
    if not os.path.exists(Rlib):
        raise RuntimeError("Unable to locate R.dll within %s" % R_HOME)

    win32api.LoadLibrary( Rlib )


# cleanup the namespace
del(os)
try:
    del(win32api)
    del(win32con)
except:
    pass


from rpy2.rinterface._rinterface import *


# wrapper in case someone changes sys.stdout:
def consolePrint(x):
    sys.stdout.write(x)

set_writeconsole(consolePrint)

def consoleFlush():
    sys.stdout.flush()

set_flushconsole(consoleFlush)

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


