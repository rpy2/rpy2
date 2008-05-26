import os, sys, re

def get_rversion(R_HOME):
    r_exec = os.path.join(R_HOME, 'bin', 'R')
    # Twist if Win32
    if sys.platform == "win32":
        rp = os.popen3('"'+r_exec+'" --version')[2]
    else:
        rp = os.popen('"'+r_exec+'" --version')
    rversion = rp.readline()
    #Twist if 'R RHOME' spits out a warning
    if rversion.startswith("WARNING"):
        rversion = rp.readline()
    m = re.match('^R version ([^ ]+) .+$', rversion)
    if m is None:
        raise Exception("Error running 'R --version':\n" + rversion)
    rversion = m.groups()[0]
    rversion = rversion.split('.')
    rversion[0] = int(rversion[0])
    rversion[1] = int(rversion[1])
    return rversion

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

rversion = get_rversion(R_HOME)
r_packversion = '%i%02i%s' %(rversion[0], rversion[1], rversion[2])
rinterface_package = 'rpy2.rinterface.rinterface_' + r_packversion



# Win32-specific code copied from RPy-1.x
# FIXME: isnt't it possible to have conditional code
# at build time ?
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

#sys.path.insert(0, os.path.join(os.path.dirname(__file__),
#                                'rinterface_' + r_packversion))
#print(sys.path[0])

del(re)
del(os)
del(sys)

del(rversion)
del(r_packversion)

rinterface = __import__(rinterface_package)

