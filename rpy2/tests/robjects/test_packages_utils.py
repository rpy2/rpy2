import pytest
import rpy2.robjects.packages_utils as p_u


def test_default_symbol_r2python():
    test_values = (
        ('foo', 'foo'),
        ('foo.bar', 'foo_bar'),
        ('foo_bar', 'foo_bar')
    )
    for provided, expected in test_values:
        assert expected == p_u.default_symbol_r2python(provided)


@pytest.mark.parametrize(
    'symbol_mapping,expected_conflict,expected_resolution',
    [({'foo_bar': ['foo.bar'],
       'foo': ['foo']},
      {},
      {}),
     ({'foo_bar': ['foo.bar', 'foo_bar'],
       'foo': ['foo']},
      {},
      {'foo_bar': ['foo_bar'],
       'foo_bar_': ['foo.bar']}),
     ({'foo_bar': ['foo.bar', 'foo_bar', 'foo_bar_'],
       'foo': ['foo']},
      {'foo_bar': ['foo.bar', 'foo_bar', 'foo_bar_']},
      {}),
    ],
    )
def test_default_symbol_resolve_noconflicts(symbol_mapping,
                                            expected_conflict,
                                            expected_resolution):
    conflicts, resolved_mapping = p_u.default_symbol_resolve(symbol_mapping)
    assert conflicts == expected_conflict
    assert resolved_mapping == expected_resolution


def test___map_symbols():
    rnames = ('foo.bar', 'foo_bar', 'foo')
    translations = {}
    (symbol_mapping,
     conflicts,
     resolutions) = p_u._map_symbols(rnames, translations)
    expected_symbol_mapping = {
        'foo_bar': ['foo.bar', 'foo_bar'],
        'foo': ['foo']
    }
    for new_symbol, old_symbols in expected_symbol_mapping.items():
        assert symbol_mapping[new_symbol] == old_symbols
    
    translations = {'foo.bar': 'foo_dot_bar'}
    (symbol_mapping,
     conflicts,
     resolutions) = p_u._map_symbols(rnames, translations)
    
    
def test__fix_map_symbols_invalidonconflict():
    msg_prefix = ''
    exception = ValueError
    symbol_mappings = {'foo': 'foo'}
    conflicts = {'foo_bar': ['foo.bar', 'foo_bar']}
    on_conflict = 'foo'
    with pytest.raises(ValueError):
        p_u._fix_map_symbols(symbol_mappings,
                             conflicts,
                             on_conflict,
                             msg_prefix,
                             exception)


def test__fix_map_symbols_conflictwarn():
    msg_prefix = ''
    exception = ValueError
    symbol_mappings = {'foo': 'foo'}
    conflicts = {'foo_bar': ['foo.bar', 'foo_bar']}
    on_conflict = 'warn'
    with pytest.warns(UserWarning):
        p_u._fix_map_symbols(symbol_mappings,
                             conflicts,
                             on_conflict,
                             msg_prefix,
                             exception)
