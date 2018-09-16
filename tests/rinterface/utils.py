from contextlib import contextmanager


@contextmanager
def obj_in_module(module, name, func):
    backup_func = getattr(module, name)
    setattr(module, name, func)
    try:
        yield
    finally:
        setattr(module, name, backup_func)

def assert_equal_sequence(x, y):
    assert type(x) is type(y)
    assert len(x) == len(y)
    assert all(x_e == y_e for x_e, y_e in zip(x, y))


def noconsole(x):
    pass
