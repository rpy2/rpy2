import pytest
import rpy2.rinterface
import rpy2.rinterface_lib.embedded
from threading import Thread
from rpy2.rinterface import embedded


class ThreadWithExceptions(Thread):
    """Wrapper around Thread allowing to record exceptions from the thread."""

    def run(self):
        self.exception = None
        try:
            self._target()
        except Exception as e:
            self.exception = e


@pytest.mark.skipif(embedded.rpy2_embeddedR_isinitialized,
                    reason='Can only be tested before R is initialized.')
def test_threading__initr():
    thread = ThreadWithExceptions(target=rpy2.rinterface_lib.embedded._initr)
    thread.start()
    thread.join()
    assert not thread.exception


@pytest.mark.skipif(embedded.rpy2_embeddedR_isinitialized,
                    reason='Can only be tested before R is initialized.')
def test_threading_initr_simple():
    # This initialization performs more post-initialization setup compared to _initr.
    # It will check whether R is initialized from the main thread.
    thread = ThreadWithExceptions(target=rpy2.rinterface.initr_simple)
    with pytest.warns(
        UserWarning,
        match=(
            r'R is not initialized by the main thread.\n'
            r'\W+Its taking over SIGINT cannot be reversed here.+'
        )
    ):
        thread.start()
        thread.join()
    assert not thread.exception
