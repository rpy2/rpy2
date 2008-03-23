
import os, os.path, sys, shutil
from distutils.core import setup, Extension
from subprocess import Popen, PIPE




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


for RHOME in RHOMES:
    RHOME = RHOME.strip()
    print('R\'s home is:%s' %RHOME)

    r_libs = [os.path.join(RHOME, 'lib'), os.path.join(RHOME, 'modules')]


    rinterface = Extension(
            "rpy2.rinterface.rinterface",
            ["rpy/rinterface/rinterface.c", ],
            include_dirs=[ os.path.join(RHOME, 'include'),],
            libraries=['R', 'Rlapack', 'Rblas'],
            library_dirs=r_libs,
            runtime_library_dirs=r_libs,
            #extra_link_args=[],
            )

    setup(name="rpython",
          version="0.0.1",
          description="Python interface to the R language",
          url="http://rpy.sourceforge.net",
          license="(L)GPL",
          ext_modules = [rinterface],
          package_dir = {'rpy2': 'rpy'},
          packages = ['rpy2', 'rpy2.robjects', 'rpy2.robjects.tests',
                      'rpy2.rinterface', 'rpy2.rinterface.tests']
          )



