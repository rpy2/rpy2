import pytest
from threading import Thread
from rpy2.rinterface import embedded


def rpy2_init():
    from rpy2.rinterface_lib.embedded import _initr
    _initr()


def rpy2_init_simple():
    from rpy2.rinterface import initr_simple
    initr_simple()


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
def test_threading():
    thread = ThreadWithExceptions(target=rpy2_init)
    thread.start()
    thread.join()
    assert not thread.exception


@pytest.mark.skipif(embedded.rpy2_embeddedR_isinitialized,
                    reason='Can only be tested before R is initialized.')
def test_threading_signal():
    thread = ThreadWithExceptions(target=rpy2_init_simple)
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
