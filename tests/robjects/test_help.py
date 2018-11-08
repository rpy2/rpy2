import pytest
import rpy2.robjects as robjects
import rpy2.robjects.help as rh
rinterface = robjects.rinterface

class TestPackage(object):

    def test_init(self):
        base_help = rh.Package('base')
        assert base_help.name == 'base'

    def test_fetch(self):
        base_help = rh.Package('base')
        f = base_help.fetch('print')
        assert 'title' in f.sections.keys()


class PageTestCase(object):
    
    def test_init(self):
        base_help = rh.Package('base')
        p = base_help.fetch('print')
        assert tuple(p.sections.keys())[0] == 'title'
    
    def test_to_docstring(self):
        base_help = rh.Package('base')
        p = base_help.fetch('print')
        ds = p.to_docstring()
        assert ds[:5] == 'title'


