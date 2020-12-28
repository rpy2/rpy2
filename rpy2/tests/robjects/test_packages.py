import io
import os
import pytest
import sys
import rpy2.robjects as robjects
import rpy2.robjects.help
import rpy2.robjects.packages as packages
import rpy2.robjects.packages_utils
from rpy2.rinterface_lib.embedded import RRuntimeError

rinterface = robjects.rinterface


class TestPackage(object):
    
    def tests_package_from_env(self):
        env = robjects.Environment()
        env['a'] = robjects.StrVector('abcd')
        env['b'] = robjects.IntVector((1,2,3))
        env['c'] = robjects.r(''' function(x) x^2''')
        pck = robjects.packages.Package(env, "dummy_package")
        assert isinstance(pck.a, robjects.Vector)
        assert isinstance(pck.b, robjects.Vector)
        assert isinstance(pck.c, robjects.Function)


    def test_new_with_dot(self):
        env = robjects.Environment()
        env['a.a'] = robjects.StrVector('abcd')
        env['b'] = robjects.IntVector((1,2,3))
        env['c'] = robjects.r(''' function(x) x^2''')
        pck = robjects.packages.Package(env, "dummy_package")
        assert isinstance(pck.a_a, robjects.Vector)
        assert isinstance(pck.b, robjects.Vector)
        assert isinstance(pck.c, robjects.Function)


    def test_new_with_dot_conflict(self):
        env = robjects.Environment()
        env['a.a_a'] = robjects.StrVector('abcd')
        env['a_a.a'] = robjects.IntVector((1,2,3))
        env['c'] = robjects.r(''' function(x) x^2''')
        with pytest.raises(packages.LibraryError):
            robjects.packages.Package(env, "dummy_package")


    def test_new_with_dot_conflict2(self):
        env = robjects.Environment()
        name_in_use = dir(packages.Package(env, "foo"))[0]
        env[name_in_use] = robjects.StrVector('abcd')
        with pytest.raises(packages.LibraryError):
            robjects.packages.Package(env, "dummy_package")

    def tests_package_repr(self):
        env = robjects.Environment()
        pck = robjects.packages.Package(env, "dummy_package")
        assert isinstance(repr(pck), str)


def test_signaturetranslatedanonymouspackage():
    rcode = """
    square <- function(x) {
    return(x^2)
    }
    
    cube <- function(x) {
    return(x^3)
    }
    """
    
    powerpack = packages.STAP(rcode, "powerpack")
    assert hasattr(powerpack, 'square')
    assert hasattr(powerpack, 'cube')


def test_installedstpackage_docstring():
    stats = robjects.packages.importr('stats',
                                      on_conflict='warn')
    assert stats.__doc__.startswith('Python representation of an R package.')


def test_installedstpackage_docstring_no_rname():
    stats = robjects.packages.importr('stats',
                                      on_conflict='warn')
    stats.__rname__ = None
    assert stats.__doc__.startswith(
        'Python representation of an R package.%s'
        '<No information available>' % os.linesep)


class TestImportr(object):

    def test_importr_stats(self):
        stats = robjects.packages.importr('stats',
                                          on_conflict='warn')
        assert isinstance(stats, robjects.packages.Package)

    def test_import_stats_with_libloc(self):
        path = os.path.dirname(
            robjects.packages_utils.get_packagepath('stats')
        )
        stats = robjects.packages.importr('stats', 
                                          on_conflict='warn',
                                          lib_loc = path)
        assert isinstance(stats, robjects.packages.Package)

    def test_import_stats_with_libloc_and_suppressmessages(self):
        path = os.path.dirname(
            robjects.packages_utils.get_packagepath('stats')
        )
        stats = robjects.packages.importr('stats',
                                          lib_loc=path,
                                          on_conflict='warn',
                                          suppress_messages=False)
        assert isinstance(stats, robjects.packages.Package)

    def test_import_stats_with_libloc_with_quote(self):
        path = 'coin"coin'

        with pytest.raises(robjects.packages.PackageNotInstalledError), \
             pytest.warns(UserWarning):
            Tmp_File = io.StringIO
            tmp_file = Tmp_File()
            try:
                stdout = sys.stdout
                sys.stdout = tmp_file
                robjects.packages.importr('dummy_inexistant', lib_loc=path)
            finally:
                sys.stdout = stdout
                tmp_file.close()

    def test_import_datasets(self):
        datasets = robjects.packages.importr('datasets')
        assert isinstance(datasets, robjects.packages.Package)
        assert isinstance(datasets.__rdata__, 
                          robjects.packages.PackageData)
        assert isinstance(robjects.packages.data(datasets), 
                          robjects.packages.PackageData)

    def test_datatsets_names(self):
        datasets = robjects.packages.importr('datasets')
        datasets_data = robjects.packages.data(datasets)
        datasets_names = tuple(datasets_data.names())
        assert len(datasets_names) > 0
        assert all(isinstance(x, str) for x in datasets_names)

    def test_datatsets_fetch(self):
        datasets = robjects.packages.importr('datasets')
        datasets_data = robjects.packages.data(datasets)
        datasets_names = tuple(datasets_data.names())
        assert isinstance(datasets_data.fetch(datasets_names[0]),
                          robjects.Environment)
        with pytest.raises(KeyError):
            datasets_data.fetch('foo_%s' % datasets_names[0])


def test_wherefrom():
    stats = robjects.packages.importr('stats', on_conflict='warn')
    rnorm_pack = robjects.packages.wherefrom('rnorm')
    assert rnorm_pack.do_slot('name')[0] == 'package:stats'


def test_installedpackages():
    instapacks = robjects.packages.InstalledPackages()
    res = instapacks.isinstalled('foo')
    assert res is False
    ncols = len(instapacks.colnames)
    for row in instapacks:
        assert ncols == len(row)
        

# TODO: Not really a unit test. The design of the code being
# tested (or not tested) probably need to be re-thought.
def test_parsedcode():
    rcode = '1+2'
    expression = rinterface.parse(rcode)
    pc = robjects.packages.ParsedCode(expression)
    assert isinstance(pc, type(expression))


def test_sourcecode():
    rcode = '1+2'
    expression = rinterface.parse(rcode)
    sc = robjects.packages.SourceCode(rcode)
    assert isinstance(sc.parse(), type(expression))


def test_sourcecode_as_namespace():
    rcode = '\n'.join(
        ('x <- 1+2',
         'f <- function(x) x+1')
    )
    sc = robjects.packages.SourceCode(rcode)
    foo_ns = sc.as_namespace('foo_ns')
    assert hasattr(foo_ns, 'x')
    assert hasattr(foo_ns, 'f')
    assert foo_ns.x[0] == 3
    assert isinstance(foo_ns.f, rinterface.SexpClosure)
