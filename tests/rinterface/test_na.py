import pytest
import math
import rpy2.rinterface as ri

ri.initr()


def test_r_to_NAInteger():
    na_int = ri.NA_Integer
    r_na_int = ri.evalr("NA_integer_")[0]
    assert r_na_int is na_int


def test_NAInteger_repr():
    na = ri.NA_Integer
    assert repr(na) == 'NA_integer_'


def test_NAInteger_str():
    na = ri.NA_Integer
    assert str(na) == 'NA_integer_'


def test_NAInteger_to_r():
    na_int = ri.NA_Integer
    assert ri.baseenv["is.na"](na_int)[0]


def test_bool_NAInteger():
    with pytest.raises(ValueError):
        bool(ri.NA_Integer)


@pytest.mark.skip(
    reason="Python changed the behavior for int-inheriting objects.")
def test_NAInteger_binaryfunc():
    na_int = ri.NAInteger
    assert (na_int + 2) is na_int


def test_NAInteger_in_vector():
    na_int = ri.NA_Integer
    x = ri.IntSexpVector((1, na_int, 2))
    assert x[1] is na_int
    assert x[0] == 1
    assert x[2] == 2


def test_R_to_NALogical():
    r_na_lgl = ri.evalr('NA')[0]
    assert r_na_lgl is ri.NA


def test_NALogical_repr():
    na = ri.NA_Logical
    assert repr(na) == 'NA'


def test_NALogical_str():
    na = ri.NA_Logical
    assert str(na) == 'NA'


def test_bool_NALogical():
    with pytest.raises(ValueError):
        bool(ri.NA)


def test_NALogical_to_r():
    na_lgl = ri.NA_Logical
    assert ri.baseenv["is.na"](na_lgl)[0] is True


def test_NALogical_in_vector():
    na_bool = ri.NA_Logical
    x = ri.BoolSexpVector((True, na_bool, False))
    assert x[0] is True
    assert x[1] is ri.NA_Logical
    assert x[2] is False


def test_R_to_NAReal():
    r_na_real = ri.evalr('NA_real_')[0]
    assert math.isnan(r_na_real)


def test_NAReal_to_r():
    na_real = ri.NA_Real
    assert ri.baseenv["is.na"](na_real)[0]


def test_bool_NAReal():
    with pytest.raises(ValueError):
        bool(ri.NA_Real)


def test_NAReal_binaryfunc():
    na_real = ri.NA_Real
    assert math.isnan(na_real + 2.0)


def test_NAReal_in_vector():
    na_float = ri.NA_Real
    x = ri.FloatSexpVector((1.1, na_float, 2.2))
    assert math.isnan(x[1])
    assert x[0] == 1.1
    assert x[2] == 2.2


def test_NAReal_repr():
    na_float = ri.NA_Real
    assert repr(na_float) == 'NA_real_'


def test_NAReal_str():
    na_float = ri.NA_Real
    assert str(na_float) == 'NA_real_'


def test_r_to_NACharacter():
    na_character = ri.NA_Character
    r_na_character = ri.evalr("NA_character_")
    assert r_na_character.typeof == ri.RTYPES.STRSXP
    assert len(r_na_character) == 1
    assert r_na_character.get_charsxp(0).rid == na_character.rid


def test_NACharacter_repr():
    na = ri.NA_Character
    assert repr(na) == 'NA_character_'


def test_NACharacter_str():
    na = ri.NA_Character
    assert str(na) == 'NA_character_'


def test_NACharacter_to_r():
    na_character = ri.NA_Character
    assert ri.baseenv["is.na"](ri.StrSexpVector((na_character, )))[0]


def test_NACharacter_in_vector():
    na_str = ri.NA_Character
    x = ri.StrSexpVector(("ab", na_str, "cd"))
    assert x[0] == 'ab'
    assert x.get_charsxp(1).rid == na_str.rid
    assert x[2] == 'cd'


def test_R_to_NAComplex():
    r_na_complex = ri.evalr('NA_complex_')[0]
    assert math.isnan(r_na_complex.real)
    assert math.isnan(r_na_complex.imag)


def test_NAComplex_to_r():
    na_complex = ri.NA_Complex
    assert ri.baseenv["is.na"](na_complex)[0]


def test_bool_NAComplex():
    with pytest.raises(ValueError):
        bool(ri.NA_Complex)
