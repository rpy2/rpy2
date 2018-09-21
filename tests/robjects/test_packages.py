import io
import pytest
import sys
import rpy2.robjects as robjects
import rpy2.robjects.packages as packages
from rpy2.rinterface import RRuntimeError

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


class TestSignatureTranslatedAnonymousPackages(object):
    string = """
   square <- function(x) {
    return(x^2)
   }

   cube <- function(x) {
    return(x^3)
   }
   """

    def test_init(self):
        powerpack = packages.STAP(self.string, "powerpack")
        assert hasattr(powerpack, 'square')
        assert hasattr(powerpack, 'cube')


class TestImportr(object):
    
    def test_importr_stats(self):
        stats = robjects.packages.importr('stats',
                                          on_conflict='warn')
        assert isinstance(stats, robjects.packages.Package)

    def test_import_stats_with_libloc(self):
        path = robjects.packages.get_packagepath('stats')
        stats = robjects.packages.importr('stats', 
                                          on_conflict='warn',
                                          lib_loc = path)
        assert isinstance(stats, robjects.packages.Package)

    def test_import_stats_with_libloc_and_suppressmessages(self):
        path = robjects.packages.get_packagepath('stats')
        stats = robjects.packages.importr('stats', lib_loc=path,
                                          on_conflict='warn',
                                          suppress_messages=False)
        assert isinstance(stats, robjects.packages.Package)

    def test_import_stats_with_libloc_with_quote(self):
        path = 'coin"coin'

        with pytest.raises(RRuntimeError):
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

        
class TestWherefrom(object):
    
    def test_wherefrom(self):
        stats = robjects.packages.importr('stats', on_conflict='warn')
        rnorm_pack = robjects.packages.wherefrom('rnorm')
        assert rnorm_pack.do_slot('name')[0] == 'package:stats'


class TestInstalledPackages(object):
    
    def test_init(self):
        instapacks = robjects.packages.InstalledPackages()
        res = instapacks.isinstalled('foo')
        assert isinstance(res, bool)
        ncols = len(instapacks.colnames)
        for row in instapacks:
            assert ncols == len(row)
        
