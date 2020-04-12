import pytest
from rpy2.robjects import packages

try:
    from rpy2.robjects.lib import dplyr
    has_dplyr = True
    msg = ''
except packages.PackageNotInstalledError as error:
    has_dplyr = False
    msg = str(error)

datasets = packages.importr('datasets')
mtcars = packages.data(datasets).fetch('mtcars')['mtcars']

@pytest.mark.skipif(not has_dplyr, reason=msg)
class TestDplyr(object):

    def test_dataframe(self):
        dataf = dplyr.DataFrame(mtcars)
        # FIXME: no testing much at the moment...
        assert isinstance(dataf, dplyr.DataFrame)

    def test_filter_nofilter_method(self):
        dataf = dplyr.DataFrame(mtcars)
        dataf_filter = dataf.filter()
        assert dataf.nrow == dataf_filter.nrow

    def test_filter_nofilter_function(self):
        dataf = dplyr.DataFrame(mtcars)
        dataf_filter = dplyr.filter(dataf)
        assert dataf.nrow == dataf_filter.nrow
        
    def test_filter_onefilter_method(self):
        dataf = dplyr.DataFrame(mtcars)
        ngear_gt_3 = len(tuple(x for x in dataf.rx2('gear') if x > 3))
        dataf_filter = dataf.filter('gear > 3')        
        assert ngear_gt_3 == dataf_filter.nrow

    def test_filter_onefilter_function(self):
        dataf = dplyr.DataFrame(mtcars)
        ngear_gt_3 = len(tuple(x for x in dataf.rx2('gear') if x > 3))
        dataf_filter = dplyr.filter(dataf, 'gear > 3')        
        assert ngear_gt_3 == dataf_filter.nrow

    def test_splitmerge_function(self):
        dataf = dplyr.DataFrame(mtcars)
        dataf_by_gear = dataf.group_by('gear')
        dataf_sum_gear = dataf_by_gear.summarize(foo='sum(gear)')
        assert type(dataf_sum_gear) is dplyr.DataFrame
    
    def test_join(self):
        dataf_a = dplyr.DataFrame(mtcars)
        dataf_b = dataf_a.mutate(foo=1)
        dataf_c = dataf_a.inner_join(dataf_b, by=dataf_a.colnames)
        all_names = list(dataf_a.colnames)
        all_names.append('foo')
        assert sorted(list(all_names)) == sorted(list(dataf_c.colnames))
        assert tuple(all_names) == tuple(dataf_c.colnames)

    def test_collect(self):
        dataf = dplyr.DataFrame(mtcars)
        dataf_collected = dataf.collect()
        # FIXME: no real test here. Just ensuring that it is returning
        #        without error
        assert type(dataf_collected) is dplyr.DataFrame
        
    def test_arrange(self):
        dataf = dplyr.DataFrame(mtcars)
        dataf_arrange = dataf.arrange('mpg')
        assert tuple(sorted(dataf.collect().rx2('mpg'))) == \
            tuple(dataf_arrange.collect().rx2('mpg'))

