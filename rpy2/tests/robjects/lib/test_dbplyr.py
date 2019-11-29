import pytest
from rpy2.robjects.packages import PackageNotInstalledError

has_dplyr = None
try:
    from rpy2.robjects.lib import dbplyr
    has_dbplyr = True
    msg = ''
except PackageNotInstalledError as error:
    has_dbplyr = False
    msg = str(error)


@pytest.mark.skipif(not has_dplyr,
                    reason=msg)
@pytest.mark.lib_dbplyr
class TestDplyr(object):

    def test_sql(self):
        sql = dbplyr.sql('count(*)')
        # FIXME: no testing much at the moment...
        assert 'sql' in sql.rclass

