import pytest
import rpy2.rinterface as ri

ri.initr()


# TODO: make this an rinterface function
def evalr(string):
    res = ri.parse(string)
    res = ri.baseenv["eval"](res)
    return res


def test_r_to_NAInteger():
    na_int = ri.NA_Integer
    r_na_int = evalr("NA_integer_")[0]
    assert r_na_int == na_int

    
def test_NAInteger_to_r():
    na_int = ri.NA_Integer
    assert ri.baseenv["is.na"](na_int)[0]

    
@pytest.mark.skip(
    reason="Python changed the behavior for int-inheriting objects.")
def test_NAInteger_binaryfunc():
    na_int = ri.NAInteger
    assert (na_int + 2) == na_int

    
def test_NAInteger_in_vector():
    na_int = ri.NA_Integer
    x = ri.IntSexpVector((1, na_int, 2))
    assert x[1] == na_int
    assert x[0] == 1
    assert x[2] == 2

    
def test_NAInteger_repr():
    na_int = ri.NA_Integer
    assert repr(na_int) == 'NA_integer_'

    
def test_R_to_NALogical():
    na_lgl = ri.NA_Logical
    r_na_lgl = evalr('NA')[0]
    assert r_na_lgl == na_lgl

    
def test_NALogical_to_r():
    na_lgl = ri.NA_Logical
    assert ri.baseenv["is.na"](na_lgl)[0] == True

    
def test_NALogical_in_vector():
    na_bool = ri.NA_Logical
    x = ri.BoolSexpVector((True, na_bool, False))
    assert x[1] == na_bool
    assert x[0] == True
    assert x[2] == False

    
def test_NAInteger_repr():
    na_bool = ri.NA_Logical
    assert repr(na_bool) == 'NA'

    
def test_R_to_NAReal():
    na_real = ri.NA_Real
    r_na_real = evalr('NA_real_')[0]
    assert r_na_real == na_real

    
def test_NAReal_to_r():
    na_real = ri.NA_Real
    assert ri.baseenv["is.na"](na_real)[0]

    
def test_NAReal_binaryfunc():
    na_real = ri.NA_Real
    assert (na_real + 2.0) == na_real

    
def test_NAReal_in_vector():
    na_float = ri.NA_Real
    x = ri.FloatSexpVector((1.1, na_float, 2.2))
    assert x[1] == na_float
    assert x[0] == 1.1
    assert x[2] == 2.2


def test_NAReal_repr():
    na_float = ri.NA_Real
    assert repr(na_float) == 'NA_real_'


def test_r_to_NACharacter():
    na_character = ri.NA_Character
    r_na_character = evalr("NA_character_")
    assert r_na_character == na_character


def test_NACharacter_to_r():
    na_character = ri.NA_Character
    assert ri.baseenv["is.na"](ri.StrSexpVector((na_character, )))[0]


def test_NACharacter_in_vector():
    na_str = ri.NA_Character
    x = ri.StrSexpVector(("ab", na_str, "cd"))
    assert x[1] == na_str
    assert x[0] == 'ab'
    assert x[2] == 'cd'

    
def test_NACharacter_repr():
    na_str = ri.NA_Character
    assert repr(na_str) == 'NA_character_'

