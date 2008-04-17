
import os, os.path, sys, shutil, re, itertools
from distutils.core import setup, Extension
from subprocess import Popen, PIPE


try:
    import ctypes
except Exception, e:
    print(e)
    print("A working 'ctypes' module is required.")
    sys.exit(1)


RHOMES = os.getenv('RHOMES')

if RHOMES is None:
    RHOMES = Popen(["R", "RHOME"], stdout=PIPE).communicate()[0].strip()
    #Twist if 'R RHOME' spits out a warning
    if RHOMES.startswith("WARNING"):
        i = RHOMES.find(os.linesep)
        RHOMES = RHOMES[i:]
    RHOMES = [RHOMES, ]
else:
    RHOMES = RHOMES.split(os.pathsep)


def get_rversion(RHOME):
    r_exec = os.path.join(RHOME, 'bin', 'R')
    rp = os.popen(r_exec+' --version')
    rversion = rp.readline()
    m = re.match('^R version ([^ ]+) .+$', rversion)
    rversion = m.groups()[0]
    rversion = [int(x) for x in rversion.split('.')]
    return rversion

def cmp_version(x, y):
    if (x[0] < y[0]):
        return -1
    if (x[0] > y[0]):
        return 1
    if (x[0] == y[0]):
        if len(x) == 1 or len(y) == 1:
            return 0
        return cmp_version(x[1:], y[1:])

rnewest = [0, 0, 0]
rversions = []
for RHOME in RHOMES:
    RHOME = RHOME.strip()
    print('R\'s home is:%s' %RHOME)
    rversion = get_rversion(RHOME)
    if (cmp_version(rversion, rnewest) == +1):
        rnewest = rversion
    rversions.append(rversion)

def doSetup(RHOME, r_packversion):
    r_libs = [os.path.join(RHOME, 'lib'), os.path.join(RHOME, 'modules')]

    pack_name = 'rpy2'
    pack_version = '0.0.1'
    if r_packversion is not None:
        pack_name = pack_name + '_' + r_packversion
        pack_version = pack_version + '_' + r_packversion

    rinterface = Extension(
            pack_name + ".rinterface.rinterface",
            ["rpy/rinterface/rinterface.c", ],
            include_dirs=[ os.path.join(RHOME, 'include'),],
            libraries=['R', 'Rlapack', 'Rblas'],
            library_dirs=r_libs,
            runtime_library_dirs=r_libs,
            #extra_link_args=[],
            )

    setup(name = "rpython",
          version = pack_version,
          description = "Python interface to the R language",
          url = "http://rpy.sourceforge.net",
          license = "(L)GPL",
          ext_modules = [rinterface],
          package_dir = {pack_name: 'rpy'},
          packages = [pack_name, 
                      pack_name+'.robjects', 
                      pack_name+'.robjects.tests',
                      pack_name+'.rinterface', 
                      pack_name+'.rinterface.tests']
          )




for rversion, RHOME in itertools.izip(rversions, RHOMES):        

    if (cmp_version(rversion, rnewest) == 0):
        r_packversion = None
        doSetup(RHOME, r_packversion)
    
    r_packversion = '%i%02i%i' %(rversion[0], rversion[1], rversion[2])
    doSetup(RHOME, r_packversion)


