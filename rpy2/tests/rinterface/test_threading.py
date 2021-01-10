import pytest
from rpy2 import rinterface
from rpy2.rinterface import embedded


def rpy2_init():
    from rpy2.rinterface_lib.embedded import _initr
    _initr()

@pytest.mark.skipif(embedded.rpy2_embeddedR_isinitialized,
                    reason='Can only be tested before R is initialized.')
def test_threading():
    from threading import Thread

    thread = Thread(target=rpy2_init)
    thread.start()
