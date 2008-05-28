import os, sys

try:
    R_HOME = os.environ["R_HOME"]
except KeyError:
    if sys.platform == 'win32':
        raise Exception("The variable R_HOME is not defined.")
    R_HOME = os.popen("R RHOME").readlines()
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

del(sys)

from rpy2.rinterface.rinterface import *

