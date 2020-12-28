import pytest
from rpy2.robjects import packages
from rpy2.robjects import rl

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
        dataf_filter = dataf.filter(rl('gear > 3'))
        assert ngear_gt_3 == dataf_filter.nrow

    def test_filter_onefilter_function(self):
        dataf = dplyr.DataFrame(mtcars)
        ngear_gt_3 = len(tuple(x for x in dataf.rx2('gear') if x > 3))
        dataf_filter = dplyr.filter(dataf, rl('gear > 3'))
        assert ngear_gt_3 == dataf_filter.nrow

    def test_group_by(self):
        dataf_a = dplyr.DataFrame(mtcars)
        dataf_g = dataf_a.group_by(rl('gear'))

    def test_splitmerge_function(self):
        dataf = dplyr.DataFrame(mtcars)
        dataf_by_gear = dataf.group_by(rl('gear'))
        dataf_avg_mpg = dataf_by_gear.summarize(foo=rl('mean(mpg)'))
        assert isinstance(dataf_avg_mpg, dplyr.DataFrame)

    def test_mutate(self):
        dataf_a = dplyr.DataFrame(mtcars)
        dataf_b = dataf_a.mutate(foo=1, bar=rl('gear+1'))
        assert type(dataf_b) is dplyr.DataFrame
        assert all(a == b for a, b in zip(dataf_a.rx2('gear'),
                                          dataf_b.rx2('gear')))
        assert all(a+1 == b for a, b in zip(dataf_a.rx2('gear'),
                                            dataf_b.rx2('bar')))

    @pytest.mark.parametrize('join_method',
                             ('inner_join', 'left_join', 'right_join',
                              'full_join'))
    def test_join(self, join_method):
        dataf_a = dplyr.DataFrame(mtcars)
        dataf_b = dataf_a.mutate(foo=1)
        dataf_c = getattr(dataf_a, join_method)(dataf_b, by=dataf_a.colnames)
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
        dataf_arrange = dataf.arrange(rl('mpg'))
        assert tuple(sorted(dataf.collect().rx2('mpg'))) == \
            tuple(dataf_arrange.collect().rx2('mpg'))

