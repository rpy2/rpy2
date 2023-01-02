"""
R help system.

"""
import os
from collections import namedtuple
import re
import sqlite3
import typing
import warnings

import rpy2.rinterface as rinterface
from rpy2.rinterface import StrSexpVector

from rpy2.robjects.packages_utils import (get_packagepath,
                                          _libpaths,
                                          _packages)
from collections import OrderedDict

tmp = rinterface.baseenv['R.Version']()
tmp_major = int(tmp[tmp.do_slot('names').index('major')][0])
tmp_minor = float(tmp[tmp.do_slot('names').index('minor')][0])
readRDS = rinterface.baseenv['readRDS']

del tmp
del tmp_major
del tmp_minor

_eval = rinterface.baseenv['eval']

NON_UNIQUE_TAGS = set((r'\alias', r'\keyword', r'\section'))


def quiet_require(name: str, lib_loc: typing.Optional[str] = None) -> bool:
    """ Load an R package /quietly/ (suppressing messages to the console). """
    if lib_loc is None:
        lib_loc = "NULL"
    expr_txt = ('suppressPackageStartupMessages(base::require(%s, lib.loc=%s))'
                % (name, lib_loc))
    expr = rinterface.parse(expr_txt)
    ok = _eval(expr)
    return ok


quiet_require('tools')
_get_namespace = rinterface.baseenv['getNamespace']
_lazyload_dbfetch = rinterface.baseenv['lazyLoadDBfetch']

tools_ns = _get_namespace(StrSexpVector(('tools',)))
_Rd_db = tools_ns['Rd_db']
_Rd_deparse = tools_ns['.Rd_deparse']

__rd_meta = os.path.join('Meta', 'Rd.rds')
__package_meta = os.path.join('Meta', 'package.rds')

p_newarg = re.compile(r'^\s*([a-zA-Z\._][a-zA-Z0-9\._]*?)\s*:\s*(.+?)\s*$')
p_desc = re.compile(r'^\s+([^\s]+.*?)\s*$')


def _Rd2txt(section_doc):
    tempfilename = rinterface.baseenv['tempfile']()[0]
    filecon = rinterface.baseenv['file'](tempfilename, open='w')
    try:
        tools_ns['Rd2txt'](
            section_doc, out=filecon, fragment=True
        )[0].split('\n')
        rinterface.baseenv['flush'](filecon)
        rinterface.baseenv['close'](filecon)
        with open(tempfilename) as fh:
            section_rows = fh.readlines()
    finally:
        os.unlink(tempfilename)
    return section_rows


def create_metaRd_db(dbcon) -> None:
    """ Create an database to store R help pages.

    dbcon: database connection (assumed to be SQLite - may or may not work
           with other databases)
    """
    dbcon.execute('''
CREATE TABLE package (
name TEXT UNIQUE,
title TEXT,
version TEXT,
description TEXT
);
''')
    dbcon.execute('''
CREATE TABLE rd_meta (
id INTEGER, file TEXT UNIQUE, name TEXT, type TEXT, title TEXT, encoding TEXT,
package_rowid INTEGER
);
''')
    dbcon.execute('''
CREATE INDEX type_idx ON rd_meta (type);
''')
    dbcon.execute('''
CREATE TABLE rd_alias_meta (
rd_meta_rowid INTEGER, alias TEXT
);
''')
    dbcon.execute('''
CREATE INDEX alias_idx ON rd_alias_meta (alias);
''')
    dbcon.commit()


def populate_metaRd_db(package_name: str, dbcon,
                       package_path: typing.Optional[str] = None) -> None:
    """ Populate a database with the meta-information
    associated with an R package: version, description, title, and
    aliases (those are what the R help system is organised around).

    - package_name: a string
    - dbcon: a database connection
    - package_path: path the R package installation (default: None)
    """
    if package_path is None:
        package_path = get_packagepath(package_name)

    rpath = StrSexpVector((os.path.join(package_path,
                                        __package_meta),))

    rds = readRDS(rpath)
    desc = rds[rds.do_slot('names').index('DESCRIPTION')]
    db_res = dbcon.execute('insert into package values (?,?,?,?)',
                           (desc[desc.do_slot('names').index('Package')],
                            desc[desc.do_slot('names').index('Title')],
                            desc[desc.do_slot('names').index('Version')],
                            desc[desc.do_slot('names').index('Description')],
                            ))
    package_rowid = db_res.lastrowid

    rpath = StrSexpVector((os.path.join(package_path,
                                        __rd_meta),))

    rds = readRDS(rpath)
    FILE_I = rds.do_slot("names").index('File')
    NAME_I = rds.do_slot("names").index('Name')
    TYPE_I = rds.do_slot("names").index('Type')
    TITLE_I = rds.do_slot("names").index('Title')
    ENCODING_I = rds.do_slot("names").index('Encoding')
    ALIAS_I = rds.do_slot("names").index('Aliases')
    for row_i in range(len(rds[0])):
        db_res = dbcon.execute('insert into rd_meta values (?,?,?,?,?,?,?)',
                               (row_i,
                                rds[FILE_I][row_i],
                                rds[NAME_I][row_i],
                                rds[TYPE_I][row_i],
                                rds[TITLE_I][row_i],
                                rds[ENCODING_I][row_i],
                                package_rowid))
        rd_rowid = db_res.lastrowid
        for alias in rds[ALIAS_I][row_i]:
            dbcon.execute('insert into rd_alias_meta values (?,?)',
                          (rd_rowid, alias))


Item = namedtuple('Item', 'name value')


class Page(object):
    """ An R documentation page.

    The original R structure is a nested sequence of components,
    corresponding to the latex-like .Rd file

    An help page is divided into sections, the names for the sections
    are the keys for the dict attribute 'sections', and a given section
    can be extracted with the square-bracket operator.

    In R, the S3 class 'Rd' is the closest entity to this class.
    """

    def __init__(self, struct_rdb: rinterface.ListSexpVector,
                 _type: str = ''):
        sections = OrderedDict()
        for elt_i in range(len(struct_rdb)):
            elt = rinterface.baseenv['['](struct_rdb, elt_i+1)
            rd_tag = elt[0].do_slot("Rd_tag")[0]
            if rd_tag in sections and rd_tag not in NON_UNIQUE_TAGS:
                warnings.warn('Section of the R doc duplicated: %s' % rd_tag)
            sections[rd_tag] = elt
        self._sections = sections
        self._type = _type

    def _section_get(self):
        return self._sections

    sections = property(_section_get, None, None,
                        'Sections in the in help page, as a dict.')

    def __getitem__(self, item):
        """ Get a section """
        return self.sections[item]

    def arguments(self) -> typing.List[Item]:
        """ Get the arguments and descriptions as a list of Item objects. """
        section_doc = self._sections.get(r'\arguments')
        res: typing.List[Item] = list()
        if section_doc is None:
            return res
        else:
            arg_name = None
            arg_desc = None
            section_rows = _Rd2txt(section_doc)
            if len(section_rows) < 3:
                return res
            for row in section_rows[2:]:
                if arg_name is None:
                    m = p_newarg.match(row)
                    if m:
                        arg_name = m.groups()[0]
                        arg_desc = [m.groups()[1]]
                else:
                    if p_desc.match(row):
                        arg_desc.append(row.strip())
                    else:
                        res.append(
                            Item(arg_name, arg_desc)
                        )
                        arg_name = None
                        arg_desc = None

            if arg_name is not None:
                res.append(
                    Item(arg_name, arg_desc)
                )
        return res

    def _get_section(self, section: str):
        section_doc = self._sections.get(section, None)
        if section_doc is None:
            res = ''
        else:
            res = _Rd2txt(section_doc)
        return res

    def description(self) -> str:
        """ Get the description of the entry """
        return self._get_section(r'\description')

    def details(self) -> str:
        """ Get the section Details for the documentation entry."""
        return self._get_section(r'\details')

    def title(self) -> str:
        """ Get the title """
        return self._get_section(r'\title')

    def value(self) -> str:
        """ Get the value returned """
        return self._get_section(r'\value')

    def seealso(self) -> str:
        """ Get the other documentation entries recommended """
        return self._get_section(r'\seealso')

    def usage(self) -> str:
        """ Get the usage for the object """
        return self._get_section(r'\usage')

    def items(self):
        """ iterator through the sections names and content
        in the documentation Page. """
        return self.sections.items()

    def iteritems(self):
        """ iterator through the sections names and content
        in the documentation Page. (deprecated, use items()) """
        warnings.warn('Use the method items().', DeprecationWarning)
        return self.sections.items()

    def to_docstring(
            self,
            section_names: typing.Optional[typing.Tuple[str, ...]] = None
    ) -> str:
        """ section_names: list of section names to consider. If None
        all sections are used.

        Returns a string that can be used as a Python docstring. """
        s = []

        if section_names is None:
            section_names = self.sections.keys()

        def walk(tree):
            if not isinstance(tree, str):
                for elt in tree:
                    walk(elt)
            else:
                s.append(tree)
                s.append(' ')

        for name in section_names:
            name_str = name[1:] if name.startswith('\\') else name
            s.append(name_str)
            s.append(os.linesep)
            s.append('-' * len(name_str))
            s.append(os.linesep)
            s.append(os.linesep)
            walk(self.sections[name])
            s.append(os.linesep)
            s.append(os.linesep)
        return ''.join(s)


class Package(object):
    """
    The R documentation page (aka help) for a package.
    """
    __package_path = None
    __package_name = None
    __aliases_info = 'aliases.rds'
    __hsearch_meta = os.path.join('Meta', 'hsearch.rds')
    __paths_info = 'paths.rds'
    __anindex_info = 'AnIndex'

    def __package_name_get(self):
        return self.__package_name

    name = property(__package_name_get, None, None,
                    'Name of the package as known by R')

    def __init__(self, package_name: str,
                 package_path: typing.Optional[str] = None):
        self.__package_name = package_name
        if package_path is None:
            package_path = get_packagepath(package_name)
        self.__package_path = package_path

        rd_meta_dbcon = sqlite3.connect(':memory:')
        create_metaRd_db(rd_meta_dbcon)
        populate_metaRd_db(package_name,
                           rd_meta_dbcon,
                           package_path=package_path)
        self._dbcon = rd_meta_dbcon

        path = os.path.join(package_path, 'help', package_name + '.rdx')
        self._rdx = readRDS(StrSexpVector((path, )))

    def fetch(self, alias: str) -> Page:
        """ Fetch the documentation page associated with a given alias.

        For S4 classes, the class name is *often* suffixed with '-class'.
        For example, the alias to the documentation for the class
        AnnotatedDataFrame in the package Biobase is
        'AnnotatedDataFrame-class'.
        """

        c = self._dbcon.execute(
            'SELECT rd_meta_rowid, alias FROM rd_alias_meta WHERE alias=?',
            (alias, )
        )
        res_alias = c.fetchall()
        if len(res_alias) == 0:
            raise HelpNotFoundError(
                'No help could be fetched',
                topic=alias, package=self.__package_name
            )

        c = self._dbcon.execute(
            'SELECT file, name, type FROM rd_meta WHERE rowid=?',
            (res_alias[0][0], )
        )
        # since the selection is on a verified rowid we are sure to
        # exactly get one row
        res_all = c.fetchall()
        rkey = StrSexpVector((res_all[0][0][:-3], ))
        _type = res_all[0][2]
        rpath = StrSexpVector(
            (os.path.join(self.package_path,
                          'help',
                          f'{self.__package_name}.rdb'),)
        )

        rdx_variables = (
            self._rdx[self._rdx.do_slot('names').index('variables')]
        )
        _eval = rinterface.baseenv['eval']
        devnull_func = rinterface.parse('function(x) {}')
        devnull_func = _eval(devnull_func)
        res = _lazyload_dbfetch(
            rdx_variables[rdx_variables.do_slot('names').index(rkey[0])],
            rpath,
            self._rdx[self._rdx.do_slot('names').index("compressed")],
            devnull_func
        )
        p_res = Page(res, _type=_type)
        return p_res

    package_path = property(lambda self: str(self.__package_path),
                            None, None,
                            'Path to the installed R package')

    def __repr__(self):
        r = 'R package %s %s' % (self.__package_name,
                                 super(Package, self).__repr__())
        return r


class HelpNotFoundError(KeyError):
    """ Exception raised when an help topic cannot be found. """
    def __init__(self, msg, topic=None, package=None):
        super(HelpNotFoundError, self).__init__(msg)
        self.topic = topic
        self.package = package


def pages(topic):
    """ Get help pages corresponding to a given topic. """
    res = list()

    for path in _libpaths():
        for name in _packages(**{'all.available': True,
                                 'lib.loc': StrSexpVector((path,))}):
            # TODO: what if the same package is installed
            #       at different locations ?
            pack = Package(name)
            try:
                page = pack.fetch(topic)
                res.append(page)
            except HelpNotFoundError:
                pass

    return tuple(res)


def docstring(
        package: Package, alias: str,
        sections: typing.Tuple[str, ...] = (r'\usage',
                                            r'\arguments')) -> str:
    """Fetch the R documentation for an alias in a package."""
    if not isinstance(package, Package):
        package = Package(package)
    page = package.fetch(alias)
    return page.to_docstring(sections)
