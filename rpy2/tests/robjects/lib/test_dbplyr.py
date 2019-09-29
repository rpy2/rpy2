import pytest

# Try to load R dplyr package, and see if it works
from rpy2.rinterface_lib.embedded import RRuntimeError
has_dplyr = None
try:
    from rpy2.robjects.lib import dbplyr
    has_dbplyr = True
except RRuntimeError:
    has_dbplyr = False


@pytest.mark.skipif(not has_dplyr, reason='R package dbplyr is not installed.')
@pytest.mark.lib_dbplyr
class TestDplyr(object):

    def test_sql(self):
        sql = dbplyr.sql('count(*)')
        # FIXME: no testing much at the moment...
        assert 'sql' in sql.rclass

