from contextlib import contextmanager


@contextmanager
def obj_in_module(module, name, obj):
    backup_obj = getattr(module, name, None)
    setattr(module, name, obj)
    try:
        yield
    finally:
        if backup_obj:
            setattr(module, name, backup_obj)

def assert_equal_sequence(x, y):
    assert type(x) is type(y)
    assert len(x) == len(y)
    assert all(x_e == y_e for x_e, y_e in zip(x, y))


def noconsole(x):
    pass
