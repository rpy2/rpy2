
import os, os.path, sys, shutil, re, itertools
from distutils.command.build_ext import build_ext as _build_ext
from distutils.command.build import build as _build

from distutils.core import setup
from distutils.core import Extension


pack_name = 'rpy2'
pack_version = __import__('rpy').__version__


class build(_build):
    user_options = _build.user_options + \
        [
        #('r-autoconfig', None,
        # "guess all configuration paths from " +\
        #     "the R executable found in the PATH " +\
        #     "(this overrides r-home)"),
        ('r-home=', None, 
         "full path for the R home to compile against " +\
             "(see r-autoconfig for an automatic configuration)"),
        ('r-home-lib=', None,
         "full path for the R shared lib/ directory " +\
             "(<r-home>/lib otherwise)"),
        ('r-home-modules=', None,
         "full path for the R shared modules/ directory " +\
             "(<r-home>/modules otherwise)") 
        ]
    boolean_options = _build.boolean_options #+ \
        #['r-autoconfig', ]


    def initialize_options(self):
        _build.initialize_options(self)
        self.r_autoconfig = None
        self.r_home = None
        self.r_home_lib = None
        self.r_home_modules = None

class build_ext(_build_ext):
    """
    -DRPY_VERBOSE
    -DRPY_DEBUG_PRESERV
    -DRPY_DEBUG_PROMISE    : evaluation of promises
    -DRPY_DEBUG_OBJECTINIT : initialization of PySexpObject
    -DRPY_DEBUG_CONSOLE    : console I/O
    -DRPY_DEBUG_COBJECT    : SexpObject passed as a CObject
    -DRPY_DEBUG_GRDEV
    """
    user_options = _build_ext.user_options + \
        [
        #('r-autoconfig', None,
        #  "guess all configuration paths from " +\
        #      "the R executable found in the PATH " +\
        #      "(this overrides r-home)"),
        ('r-home=', None, 
         "full path for the R home to compile against " +\
             "(see r-autoconfig for an automatic configuration)"),
        ('r-home-lib=', None,
         "full path for the R shared lib/ directory" +\
             "(<r-home>/lib otherwise)"),
        ('r-home-modules=', None,
         "full path for the R shared modules/ directory" +\
             "(<r-home>/modules otherwise)")]

    boolean_options = _build_ext.boolean_options #+ \
        #['r-autoconfig', ]

    def initialize_options(self):
        _build_ext.initialize_options(self)
        self.r_autoconfig = None
        self.r_home = None
        self.r_home_lib = None
        self.r_home_modules = None

    def finalize_options(self):
        self.set_undefined_options('build',
                                   #('r_autoconfig', 'r_autoconfig'),
                                   ('r_home', 'r_home'))
        _build_ext.finalize_options(self) 
        if self.r_home is None:
            self.r_home = os.popen("R RHOME").readlines()
            if len(self.r_home) == 0:
                raise SystemExit("Error: Tried to guess R's HOME but no R command in the PATH.")

    #Twist if 'R RHOME' spits out a warning
            if self.r_home[0].startswith("WARNING"):
                self.r_home = self.r_home[1]
            else:
                self.r_home = self.r_home[0]
            #self.r_home = [self.r_home, ]

        if self.r_home is None:
            raise SystemExit("Error: --r-home not specified.")
        else:
            self.r_home = self.r_home.split(os.pathsep)

        rversions = []
        for r_home in self.r_home:
            r_home = r_home.strip()
        rversion = get_rversion(r_home)
        if cmp_version(rversion[:2], [2, 8]) == -1:
            raise SystemExit("Error: R >= 2.8 required.")
        rversions.append(rversion)

        r_libs = []
        if self.r_home_lib is None:
            r_libs.extend([os.path.join(r_home, 'lib'), ])
        else:
            r_libs.extend([self.r_home_lib, ])

        if self.r_home_modules is None:
            r_libs.extend([os.path.join(r_home, 'modules'), ])
        else:
            r_libs.extends([self.r_home_modules, ])
            
        self.library_dirs.extend(r_libs)

        include_dirs = get_rconfig(r_home, '--cppflags')[0].split()
        
        for i, d in enumerate(include_dirs):
            if d.startswith('-I'):
                include_dirs[i] = d[2:]
            else:
                raise SystemExit('Error: trouble with R configuration %s' %d)
        self.include_dirs.extend(include_dirs)

        extra_link_args = get_rconfig(r_home, '--ldflags') +\
            get_rconfig(r_home, 'LAPACK_LIBS', 
                        allow_empty=True) +\
                        get_rconfig(r_home, 'BLAS_LIBS')

        for e in self.extensions:
            e.extra_compile_args.extend(extra_link_args)

    def run(self):
        _build_ext.run(self)



def get_rversion(r_home):
    r_exec = os.path.join(r_home, 'bin', 'R')
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
    rversion = m.groups()[0]
    rversion = rversion.split('.')
    rversion[0] = int(rversion[0])
    rversion[1] = int(rversion[1])
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

def get_rconfig(r_home, about, allow_empty = False):
    r_exec = os.path.join(r_home, 'bin', 'R')
    cmd = '"'+r_exec+'" CMD config '+about
    rp = os.popen(cmd)
    rconfig = rp.readline()
    #Twist if 'R RHOME' spits out a warning
    if rconfig.startswith("WARNING"):
        rconfig = rp.readline()
    rconfig = rconfig.strip()
    #sanity check of what is returned into rconfig
    rconfig_m = None
    possible_patterns = ('^(-L.+) (-l.+)$',
                         '^(-l.+)$',  # fix for the case -lblas is returned
                         '^(-F.+? -framework .+)$', # fix for MacOS X
                         '^(-framework .+)$',
                         '^(-I.+)$')
    for pattern in possible_patterns:
        rconfig_m = re.match(pattern, rconfig)
        if rconfig_m is not None:
            break
    if rconfig_m is None:
        if allow_empty and (rconfig == ''):
            print(cmd + '\nreturned an empty string.\n')
            return ()
        else:
            raise Exception(cmd + '\nreturned\n' + rconfig)
    return rconfig_m.groups()


def getRinterface_ext():
    #r_libs = [os.path.join(RHOME, 'lib'), os.path.join(RHOME, 'modules')]
    r_libs = []

    #FIXME: crude way (will break in many cases)
    #check how to get how to have a configure step
    define_macros = []

    if sys.platform == 'win32':
        define_macros.append(('Win32', 1))
    else:
        define_macros.append(('R_INTERFACE_PTRS', 1))
        define_macros.append(('HAVE_POSIX_SIGJMP', 1))

    define_macros.append(('CSTACK_DEFNS', 1))
    define_macros.append(('RIF_HAS_RSIGHAND', 1))

    include_dirs = []
    
    rinterface_ext = Extension(
            name = pack_name + '.rinterface.rinterface',
            sources = [ \
            #os.path.join('rpy', 'rinterface', 'embeddedr.c'), 
            #os.path.join('rpy', 'rinterface', 'r_utils.c'),
            #os.path.join('rpy', 'rinterface', 'buffer.c'),
            #os.path.join('rpy', 'rinterface', 'sequence.c'),
            #os.path.join('rpy', 'rinterface', 'sexp.c'),
            os.path.join('rpy', 'rinterface', 'rinterface.c')
                       ],
            depends = [os.path.join('rpy', 'rinterface', 'embeddedr.h'), 
                       os.path.join('rpy', 'rinterface', 'r_utils.h'),
                       os.path.join('rpy', 'rinterface', 'buffer.h'),
                       os.path.join('rpy', 'rinterface', 'sequence.h'),
                       os.path.join('rpy', 'rinterface', 'sexp.h'),
                       os.path.join('rpy', 'rinterface', 'rpy_rinterface.h')
                       ],
            include_dirs = [os.path.join('rpy', 'rinterface'),] + include_dirs,
            libraries = ['R', ],
            library_dirs = r_libs,
            define_macros = define_macros,
            runtime_library_dirs = r_libs,
            #extra_compile_args=['-O0', '-g'],
           
            )

    rpy_device_ext = Extension(
        pack_name + '.rinterface.rpy_device',
            [
            os.path.join('rpy', 'rinterface', 'rpy_device.c'),
             ],
            include_dirs = include_dirs + 
                            [os.path.join('rpy', 'rinterface'), ],
            libraries = ['R', ],
            library_dirs = r_libs,
            define_macros = define_macros,
            runtime_library_dirs = r_libs,
            #extra_compile_args=['-O0', '-g'],
        )

    return [rinterface_ext, rpy_device_ext]


rinterface_exts = []
ri_ext = getRinterface_ext()
rinterface_exts.append(ri_ext)

pack_dir = {pack_name: 'rpy'}

import distutils.command.install
for scheme in distutils.command.install.INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

setup(
    #install_requires=['distribute'],
    cmdclass = {'build': build,
                'build_ext': build_ext},
    name = pack_name,
    version = pack_version,
    description = "Python interface to the R language",
    url = "http://rpy.sourceforge.net",
    license = "AGPLv3.0 (except rpy2.rinterface: LGPL)",
    author = "Laurent Gautier",
    author_email = "lgautier@gmail.com",
    ext_modules = rinterface_exts[0],
    package_dir = pack_dir,
    packages = [pack_name,
                pack_name + '.rlike',
                pack_name + '.rlike.tests',
                pack_name + '.rinterface',
                pack_name + '.rinterface.tests',
                pack_name + '.robjects',
                pack_name + '.robjects.tests',
                pack_name + '.robjects.lib',
                ],
    classifiers = ['Programming Language :: Python',
                   'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
                   'License :: OSI Approved :: GNU Affero General Public License v3',
                   'Intended Audience :: Developers',
                   'Intended Audience :: Science/Research',
                   'Development Status :: 4 - Beta'
                   ],
    data_files = [(os.path.join('rpy2', 'images'), 
                   [os.path.join('doc', 'source', 'rpy2_logo.png')])]
    
    #[pack_name + '.rinterface_' + x for x in rinterface_rversions] + \
        #[pack_name + '.rinterface_' + x + '.tests' for x in rinterface_rversions]
    )

