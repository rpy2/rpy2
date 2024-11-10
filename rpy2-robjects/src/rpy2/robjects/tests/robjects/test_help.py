import os
import pytest
import rpy2.robjects as robjects
import rpy2.robjects.help as rh
rinterface = robjects.rinterface


class TestPackage(object):

    def test_init(self):
        base_help = rh.Package('base')
        assert base_help.name == 'base'

    def test_repr(self):
        base_help = rh.Package('base')
        assert isinstance(repr(base_help), str)


class TestPage(object):
    
    def test_init(self):
        base_help = rh.Package('base')
        p = base_help.fetch('print')
        assert tuple(p.sections.keys())[0] == '\\title'

    def test_fetch(self):
        base_help = rh.Package('base')
        f = base_help.fetch('print')
        assert '\\title' in f.sections.keys()

    def test_to_docstring(self):
        base_help = rh.Package('base')
        p = base_help.fetch('print')
        ds = p.to_docstring()
        assert ds[:5] == 'title'

    def test_title(self):
        base_help = rh.Package('base')
        p = base_help.fetch('print')
        d = p.title()
        assert all(isinstance(x, str) for x in d)
        assert len(d) > 0

    def test_description(self):
        base_help = rh.Package('base')
        p = base_help.fetch('print')
        d = p.description()
        assert all(isinstance(x, str) for x in d)
        assert len(d) > 0

    def test_seealso(self):
        base_help = rh.Package('base')
        p = base_help.fetch('print')
        d = p.seealso()
        assert all(isinstance(x, str) for x in d)
        assert len(d) > 0

    def test_usage(self):
        base_help = rh.Package('base')
        p = base_help.fetch('print')
        d = p.usage()
        assert all(isinstance(x, str) for x in d)
        assert len(d) > 0
        
    def test_iteritems(self):
        base_help = rh.Package('base')
        p = base_help.fetch('print')
        with pytest.deprecated_call():
            res = tuple(p.iteritems())
        # TODO: test result more in depth.
        assert len(res) > 0

    def test_iteritems(self):
        base_help = rh.Package('base')
        p = base_help.fetch('print')
        res = tuple(p.items())
        # TODO: test result more in depth.
        assert len(res) > 0

@pytest.mark.xfail(
    os.name == 'nt',
    reason='Windows is missing library/translations/Meta/Rd.rds file')
def test_pages():
    pages = rh.pages('plot')
    assert isinstance(pages, tuple)
    assert all(isinstance(elt, rh.Page) for elt in pages)
