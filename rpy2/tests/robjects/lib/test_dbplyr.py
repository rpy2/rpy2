import pytest
from rpy2.robjects import packages

has_dbplyr = None
try:
    from rpy2.robjects.lib import dbplyr
    has_dbplyr = True
    msg = ''
except packages.PackageNotInstalledError as error:
    has_dbplyr = False
    msg = str(error)


@pytest.mark.skipif(not has_dbplyr,
                    reason=msg)
class TestDplyr(object):

    def test_sql(self):
        sql = dbplyr.sql('count(*)')
        # FIXME: no testing much at the moment...
        assert 'sql' in sql.rclass

