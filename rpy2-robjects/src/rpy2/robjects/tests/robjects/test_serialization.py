import pytest
import pickle
import tempfile

from rpy2 import robjects


def test_pickle():
    tmp_file = tempfile.NamedTemporaryFile()
    robj = robjects.baseenv["pi"]
    pickle.dump(robj, tmp_file)
    tmp_file.flush()
    tmp_file.seek(0)
    robj_again = pickle.load(tmp_file)
    tmp_file.close()

    assert isinstance(robj, robjects.FloatVector)

    # Check that underlying R objects are identical.
    assert robjects.baseenv["identical"](robj,
                                         robj_again)[0]
    # Check the instance dict is also identical
    assert set(robj.__dict__.keys()) == set(robj_again.__dict__.keys())

