import pytest

from rpy2.robjects import packages

try:
    from rpy2.robjects.lib import tidyr
    has_tidyr = True
    msg = ''
except packages.PackageNotInstalledError as error:
    has_tidyr = False
    msg = str(error)

from rpy2 import rinterface
from rpy2.robjects import vectors
datasets = packages.importr('datasets')
mtcars = packages.data(datasets).fetch('mtcars')['mtcars']

@pytest.mark.skipif(not has_tidyr,
                    reason=msg)
class TestTidyr(object):

    def test_dataframe(self):
        dataf = tidyr.DataFrame(
            {'x': vectors.IntVector((1,2,3,4,5)),
             'labels': vectors.StrVector(('a','b','b','b','a'))})
        assert isinstance(dataf, tidyr.DataFrame)
        assert sorted(['x', 'labels']) == sorted(list(dataf.colnames))
        
    def test_spread(self):
        labels = ('a','b','c','d','e')
        dataf = tidyr.DataFrame(
            {'x': vectors.IntVector((1,2,3,4,5)),
             'labels': vectors.StrVector(labels)})
        dataf_spread = dataf.spread('labels',
                                    'x')
        assert sorted(list(labels)) == sorted(list(dataf_spread.colnames))

    def test_gather(self):
        dataf = tidyr.DataFrame({'a': 1.0, 'b': 2.0})
        dataf_gathered = dataf.gather('label',
                                      'x')
        assert sorted(['label', 'x']) == sorted(list(dataf_gathered.colnames))
