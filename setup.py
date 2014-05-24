
import os, os.path, sys, shutil, re, itertools, warnings
import argparse, shlex
from collections import namedtuple
from distutils.command.build_ext import build_ext as _build_ext
from distutils.command.build import build as _build

from setuptools import setup
from distutils.core import Extension

pack_name = 'rpy2'
pack_version = __import__('rpy').__version__

default_lib_directory = 'bin' if sys.platform=='win32' else 'lib'

package_prefix='.'
from distutils.core import setup    
from distutils.core import Extension


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
            "(<r-home>/%s otherwise)" % default_lib_directory),
        ('r-home-modules=', None,
         "full path for the R shared modules/ directory " +\
             "(<r-home>/modules otherwise)"),
        ('ignore-check-rversion', None, 'ignore checks for supported R versions')]

    boolean_options = _build.boolean_options + \
        ['ignore_check_rversion', ]

    def initialize_options(self):
        _build.initialize_options(self)
        self.r_autoconfig = None
        self.r_home = None
        self.r_home_lib = None
        self.ignore_check_rversion = False


class build_ext(_build_ext):
    """
    -DRPY_STRNDUP          : definition of strndup()
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
            "(<r-home>/%s otherwise)" % default_lib_directory),
        ('r-home-modules=', None,
         "full path for the R shared modules/ directory" +\
             "(<r-home>/modules otherwise)"),
        ('ignore-check-rversion', None, 'ignore checks for supported R versions')]

    boolean_options = _build_ext.boolean_options + \
        ['ignore-check-rversion', ] #+ \
        #['r-autoconfig', ]

    def initialize_options(self):
        _build_ext.initialize_options(self)
        self.r_autoconfig = None
        self.r_home = None
        self.r_home_lib = None
        self.ignore_check_rversion = False

    def finalize_options(self):
        self.set_undefined_options('build',
                                   #('r_autoconfig', 'r_autoconfig'),
                                   ('r_home', 'r_home'))

        _build_ext.finalize_options(self) 
        if self.r_home is None:
            tmp = os.popen("R RHOME")
            self.r_home = tmp.readlines()
            tmp.close()
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
        if rversion[0] == 'development' or \
                cmp_version(rversion[:2], [2, 8]) == -1:
            if self.ignore_check_rversion:
                warnings.warn("R did not seem to have the minimum required version number")
            else:
                raise SystemExit("Error: R >= 2.8 required (and R told '%s')." %'.'.join(rversion))    
        rversions.append(rversion)

        config = RConfig()
        for about in ('--ldflags', '--cppflags'):
            config += get_rconfig(r_home, about)
        for about in ('LAPACK_LIBS', 'BLAS_LIBS'):
            config += get_rconfig(r_home, about, True)

        print(config.__repr__())

        self.include_dirs.extend(config._include_dirs)
        self.libraries.extend(config._libraries)
        self.library_dirs.extend(config._library_dirs)

        #for e in self.extensions:
        #    self.extra_link_args.extra_link_args(config.extra_link_args)
        #    e.extra_compile_args.extend(extra_link_args)

    def run(self):
        _build_ext.run(self)



def get_rversion(r_home):
    r_exec = os.path.join(r_home, 'bin', 'R')
    # Twist if Win32
    if sys.platform == "win32":
        if "64 bit" in sys.version:
            r_exec = os.path.join(r_home, 'bin', 'x64', 'R')
        if sys.version_info >= (3,):
            import subprocess
            p = subprocess.Popen('"'+r_exec+'" --version',
                                 shell=True,
                                 stdin=subprocess.PIPE, 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.STDOUT, 
                                 close_fds=sys.platform!="win32")
            rp = p.stdout
        else:
            rp = os.popen3('"'+r_exec+'" --version')[2]
    else:
        rp = os.popen('"'+r_exec+'" --version')
    rversion = rp.readline()
    #Twist if 'R RHOME' spits out a warning
    if rversion.startswith("WARNING"):
        rversion = rp.readline()
    m = re.match('^R ([^ ]+) ([^ ]+) .+$', rversion)
    if m is None:
        rp.close()
        # return dummy version 0.0
        rversion = [0, 0]
    else:
        rversion = m.groups()[1]
        if m.groups()[0] == 'version':
            rversion = rversion.split('.')
            rversion[0] = int(rversion[0])
            rversion[1] = int(rversion[1])
        else:
            rversion = ['development', '']
    rp.close()
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

class RConfig(object):
    _include_dirs = None
    _libraries = None
    _library_dirs = None 
    _extra_link_args = None
    _extra_compile_args = None
    _frameworks = None
    _framework_dirs = None

    parser = argparse.ArgumentParser()
    parser.add_argument('-L', dest='library_dirs', nargs='*')
    parser.add_argument('-l', dest='libraries', nargs='*')
    parser.add_argument('-I', dest='include_dirs', nargs='*')
    parser.add_argument('-F', dest='framework_dirs', nargs='*')
    parser.add_argument('-framework', dest='frameworks', nargs='*')
    #parser.add_argument('-Wl', dest='extra_link_args', nargs='*')
    #parser.add_argument('-f', dest='extra_link_args', nargs='*')

    def __init__(self,
                 include_dirs = tuple(), libraries = tuple(),
                 library_dirs = tuple(), extra_link_args = tuple(),
                 extra_compile_args = tuple(),
                 frameworks = tuple(),
                 framework_dirs = tuple()):
        for k in ('include_dirs', 'libraries', 
                  'library_dirs', 'extra_link_args',
                  'extra_compile_args'):
            v = locals()[k]
            if not isinstance(v, tuple):
                if isinstance(v, str):
                    v = [v, ]
            v = tuple(set(v))
            setattr(self, '_'+k, v)
        # frameworks are specific to OSX
        for k in ('framework_dirs', 'frameworks'):
            v = locals()[k]
            if not isinstance(v, tuple):
                if isinstance(v, str):
                    v = [v, ]
            v = tuple(set(v))
            setattr(self, '_'+k, v)
            self._extra_link_args = tuple(set(v + self._extra_link_args))

    @staticmethod
    def from_string(string, allow_empty = False):
        # sanity check of what is returned into rconfig
        rconfig_m = None        
        span = (0, 0)
        rc = RConfig()
        args, extra_args = RConfig.parser.parse_known_args(shlex.split(string))
        d = dict()
        for n in dir(args):
            if n.startswith('_'):
                continue
            a = getattr(args, n)
            if a is None:
                continue
            d[n] = a
        if 'extra_link_args' in d:
            d['extra_link_args'].append(extra_args)
        else:
            d['extra_link_args'] = extra_args            
        rc = RConfig(**d)
        return rc
            
    def __repr__(self):
        s = 'Configuration for R as a library:' + os.linesep
        s += os.linesep.join(
            ['  ' + x + ': ' + self.__dict__['_'+x].__repr__() \
                 for x in ('include_dirs', 'libraries',
                           'library_dirs', 'extra_link_args')])
        s += os.linesep + ' # OSX-specific (included in extra_link_args)' + os.linesep 
        s += os.linesep.join(
            ['  ' + x + ': ' + self.__dict__['_'+x].__repr__() \
                 for x in ('framework_dirs', 'frameworks')]
            )
        
        return s

    def __add__(self, config):
        assert isinstance(config, RConfig)
        res = RConfig(include_dirs = self._include_dirs + \
                          config._include_dirs,
                      libraries = self._libraries + config._libraries,
                      library_dirs = self._library_dirs + \
                          config._library_dirs,
                      extra_link_args = self._extra_link_args + \
                          config._extra_link_args,
                      frameworks = self._frameworks + config._frameworks,
                      framework_dirs = self._framework_dirs + config._framework_dirs)
        return res


def get_rconfig(r_home, about, allow_empty = False):
    if sys.platform == "win32" and "64 bit" in sys.version:
        r_exec = os.path.join(r_home, 'bin', 'x64', 'R')
    else:
        r_exec = os.path.join(r_home, 'bin', 'R')
    cmd = '"'+r_exec+'" CMD config '+about
    print(cmd)
    rp = os.popen(cmd)
    rconfig = rp.readline()
    #Twist if 'R RHOME' spits out a warning
    if rconfig.startswith("WARNING"):
        rconfig = rp.readline()
    rconfig = rconfig.strip()
    try:
        rc = RConfig.from_string(rconfig, allow_empty = allow_empty)
    except ValueError as ve:
        print(ve)
        sys.exit("Problem while running `{0}`\n".format(cmd))
    rp.close()
    return rc

def getRinterface_ext():
    #r_libs = [os.path.join(RHOME, 'lib'), os.path.join(RHOME, 'modules')]
    r_libs = []
    extra_link_args = []
    extra_compile_args = []

    #FIXME: crude way (will break in many cases)
    #check how to get how to have a configure step
    define_macros = []

    if sys.platform == 'win32':
        define_macros.append(('Win32', 1))
        if "64 bit" in sys.version:
            define_macros.append(('Win64', 1))
            extra_link_args.append('-m64')
            extra_compile_args.append('-m64')
            # MS_WIN64 only defined by pyconfig.h for MSVC. 
            # See http://bugs.python.org/issue4709
            define_macros.append(('MS_WIN64', 1))
    else:
        define_macros.append(('R_INTERFACE_PTRS', 1))
        define_macros.append(('HAVE_POSIX_SIGJMP', 1))
        define_macros.append(('RIF_HAS_RSIGHAND', 1))
        define_macros.append(('CSTACK_DEFNS', 1))
        define_macros.append(('HAS_READLINE', 1))


    if sys.byteorder == 'big':
        define_macros.append(('RPY_BIGENDIAN', 1))
    else:
        pass

    include_dirs = []
    
    rinterface_ext = Extension(
            name = pack_name + '.rinterface._rinterface',
            sources = [ \
            #os.path.join('rpy', 'rinterface', 'embeddedr.c'), 
            #os.path.join('rpy', 'rinterface', 'r_utils.c'),
            #os.path.join('rpy', 'rinterface', 'buffer.c'),
            #os.path.join('rpy', 'rinterface', 'sequence.c'),
            #os.path.join('rpy', 'rinterface', 'sexp.c'),
            os.path.join(package_prefix,
                         'rpy', 'rinterface', '_rinterface.c')
                       ],
            depends = [os.path.join(package_prefix,
                                    'rpy', 'rinterface', 'embeddedr.h'), 
                       os.path.join(package_prefix,
                                    'rpy', 'rinterface', 'r_utils.h'),
                       os.path.join(package_prefix,
                                    'rpy', 'rinterface', 'buffer.h'),
                       os.path.join(package_prefix,
                                    'rpy', 'rinterface', 'sequence.h'),
                       os.path.join(package_prefix,
                                    'rpy', 'rinterface', 'sexp.h'),
                       os.path.join(package_prefix,
                                    'rpy', 'rinterface', '_rinterface.h'),
                       os.path.join(package_prefix,
                                    'rpy', 'rinterface', 'rpy_device.h')
                       ],
            include_dirs = [os.path.join(package_prefix,
                                         'rpy', 'rinterface'),] + include_dirs,
            libraries = ['R', ],
            library_dirs = r_libs,
            define_macros = define_macros,
            runtime_library_dirs = r_libs,
            extra_compile_args=extra_compile_args,
            #extra_compile_args=['-O0', '-g'],
            extra_link_args = extra_link_args
            )

    rpy_device_ext = Extension(
        pack_name + '.rinterface._rpy_device',
        [
            os.path.join(package_prefix,
                         'rpy', 'rinterface', '_rpy_device.c'),
            ],
        include_dirs = include_dirs + 
        [os.path.join('rpy', 'rinterface'), ],
        libraries = ['R', ],
        library_dirs = r_libs,
        define_macros = define_macros,
        runtime_library_dirs = r_libs,
        extra_compile_args=extra_compile_args,
        #extra_compile_args=['-O0', '-g'],
        extra_link_args = extra_link_args
        )

    return [rinterface_ext, rpy_device_ext]

if __name__ == '__main__':
    rinterface_exts = []
    ri_ext = getRinterface_ext()
    rinterface_exts.append(ri_ext)

    pack_dir = {pack_name: os.path.join(package_prefix, 'rpy')}

    import distutils.command.install
    for scheme in distutils.command.install.INSTALL_SCHEMES.values():
        scheme['data'] = scheme['purelib']

    setup(
        #install_requires=['distribute'],
        cmdclass = {'build': build,
                    'build_ext': build_ext},
        name = pack_name,
        version = pack_version,
        description = "Python interface to the R language (embedded R)",
        url = "http://rpy.sourceforge.net",
        license = "GPLv2+",
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
                    pack_name + '.robjects.lib.tests',
                    pack_name + '.interactive',
                    pack_name + '.interactive.tests',
                    pack_name + '.ipython',
                    pack_name + '.ipython.tests'
                    ],
        classifiers = ['Programming Language :: Python',
                       'Programming Language :: Python :: 3',
                       'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
                       'Intended Audience :: Developers',
                       'Intended Audience :: Science/Research',
                       'Development Status :: 5 - Production/Stable'
                       ],
        package_data = {
            'rpy2': ['images/*.png', ],
            'rpy2': ['doc/source/rpy2_logo.png', ]}

        #[pack_name + '.rinterface_' + x for x in rinterface_rversions] + \
            #[pack_name + '.rinterface_' + x + '.tests' for x in rinterface_rversions]
        )

