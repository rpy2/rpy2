import pytest
from rpy2 import rinterface
from rpy2.rinterface import embedded


@pytest.mark.skipif(embedded.rpy2_embeddedR_isinitialized,
                    reason='This test should be run independently of other tests.')
def test_endr():
    rinterface.initr()
    embedded.endr(1)
    assert (embedded.rpy2_embeddedR_isinitialized &
            embedded.RPY_R_Status.ENDED.value) == embedded.RPY_R_Status.ENDED.value

