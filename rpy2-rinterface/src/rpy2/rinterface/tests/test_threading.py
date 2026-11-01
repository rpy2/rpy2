import os
import pytest
import rpy2.rinterface
import rpy2.rinterface_lib.embedded
from threading import Thread


class ThreadWithExceptions(Thread):
    """Wrapper around Thread allowing to record exceptions from the thread."""

    def run(self):
        self.exception = None
        try:
            self._target()
        except Exception as e:
            self.exception = e


@pytest.mark.skipif(rpy2.rinterface_lib.embedded.rpy2_embeddedR_isinitialized,
                    reason='Can only be tested before R is initialized.')
@pytest.mark.skipif(os.name == 'nt',
                    reason='Crashes Python on Windows.')
def test_threading__initr():
    thread = ThreadWithExceptions(target=rpy2.rinterface_lib.embedded._initr)
    thread.start()
    thread.join()
    assert not thread.exception
