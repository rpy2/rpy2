import pytest
import rpy2.rinterface as ri

ri.initr()


def test_r_to_NAInteger():
    na_int = ri.NAIntegerType()
    r_na_int = evalr("NA_integer_")[0]
    assert r_na_int is na_int

    
def test_NAInteger_to_r():
    na_int = ri.NAIntegerType()
    assert ri.baseenv["is.na"](na_int)[0]

    
@pytest.mark.skip(
    reason="Python changed the behavior for int-inheriting objects.")
def test_NAInteger_binaryfunc():
    na_int = ri.NAIntegerType()
    assert (na_int + 2) is na_int

    
def test_NAInteger_in_vector():
    na_int = ri.NAIntegerType()
    x = ri.IntSexpVector((1, na_int, 2))
    assert x[1] is na_int
    assert x[0] == 1
    assert x[2] == 2

    
def test_NAInteger_repr():
    na_int = ri.NAIntegerType()
    assert repr(na_int) == 'NA_integer_'

    
def test_R_to_NALogical():
    na_lgl = ri.NALogicalType()
    r_na_lgl = evalr('NA')[0]
    assert r_na_lgl is na_lgl

    
def test_NALogical_to_r():
    na_lgl = ri.NALogicalType()
    assert ri.baseenv["is.na"](na_lgl)[0] == True

    
def test_NALogical_in_vector():
    na_bool = ri.NALogicalType()
    x = ri.BoolSexpVector((True, na_bool, False))
    assert x[1] is na_bool
    assert x[0] == True
    assert x[2] == False

    
def test_NAInteger_repr():
    na_bool = ri.NALogicalType()
    assert repr(na_bool) == 'NA'

    
def test_R_to_NAReal():
    na_real = ri.NARealType()
    r_na_real = evalr('NA_real_')[0]
    assert r_na_real is na_real

    
def test_NAReal_to_r():
    na_real = ri.NARealType()
    assert ri.baseenv["is.na"](na_real)[0]

    
def test_NAReal_binaryfunc():
    na_real = ri.NARealType()
    assert (na_real + 2.0) is na_real

    
def test_NAReal_in_vector():
    na_float = ri.NARealType()
    x = ri.FloatSexpVector((1.1, na_float, 2.2))
    assert x[1] is na_float
    assert x[0] == 1.1
    assert x[2] == 2.2


def test_NAReal_repr():
    na_float = ri.NARealType()
    assert repr(na_float) == 'NA_real_'


def test_r_to_NACharacter():
    na_character = ri.NACharacterType()
    r_na_character = evalr("NA_character_")[0]
    assert r_na_character is na_character


def test_NACharacter_to_r():
    na_character = ri.NACharacterType()
    assert ri.baseenv["is.na"](ri.StrSexpVector((na_character, )))[0]


def test_NACharacter_in_vector():
    na_str = ri.NACharacterType()
    x = ri.StrSexpVector(("ab", na_str, "cd"))
    assert x[1] is na_str
    assert x[0] == 'ab'
    assert x[2] == 'cd'

    
def test_NACharacter_repr():
    na_str = ri.NACharacterType()
    assert repr(na_str) == 'NA_character_'

