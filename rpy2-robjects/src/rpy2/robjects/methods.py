import abc
from types import SimpleNamespace
import typing
from rpy2.robjects.robject import RObjectMixin
import rpy2.rinterface as rinterface
from rpy2.rinterface import StrSexpVector
from rpy2.robjects import help as rhelp
from rpy2.robjects import conversion

_get_exported_value = rinterface.baseenv['::']
getmethod = _get_exported_value('methods', 'getMethod')


require = rinterface.baseenv.find('require')
require(StrSexpVector(('methods', )),
        quietly=rinterface.BoolSexpVector((True, )))


class RS4(RObjectMixin, rinterface.SexpS4):
    """ Python representation of an R instance of class 'S4'. """

    def slotnames(self):
        """ Return the 'slots' defined for this object """
        return methods_env['slotNames'](self)

    def do_slot(self, name):
        return (conversion.get_conversion()
                .rpy2py(super(RS4, self).do_slot(name)))

    def extends(self):
        """Return the R classes this extends.

        This calls the R function methods::extends()."""
        return methods_env['extends'](self.rclass)

    @staticmethod
    def isclass(name):
        """ Return whether the given name is a defined class. """
        name = conversion.get_conversion().py2rpy(name)
        return methods_env['isClass'](name)[0]

    def validobject(self, test=False, complete=False):
        """ Return whether the instance is 'valid' for its class. """
        cv = conversion.get_conversion()
        test = cv.py2rpy(test)
        complete = cv.py2rpy(complete)
        return methods_env['validObject'](self, test=test,
                                          complete=complete)[0]


class ClassRepresentation(RS4):
    """Definition of an R S4 class.

    This can be thought of as the Python "type" (class definition)
    for an R object with the C-level type S4.
    """

    @property
    def slots(self):
        """Slots (attributes) for the class."""
        return [y[0] for y in self.do_slot('slots')]

    @property
    def basenames(self):
        """Parent classes."""
        return [y[0] for y in self.do_slot('contains')]

    contains = basenames

    @property
    def isabstract(self):
        """Is the class an abstract class ?"""
        return self.do_slot('virtual')[0]

    virtual = isabstract

    @property
    def packagename(self):
        """R package in which the class is defined."""
        return self.do_slot('package')[0]

    package = packagename

    @property
    def classname(self):
        """Name of the R class."""
        return self.do_slot('className')[0],


def getclassdef(cls_name: str, packagename: typing.Optional[str] = None):
    package: typing.Union[rinterface._MissingArgType, StrSexpVector]
    if packagename is None:
        package = rinterface.MissingArg
    else:
        package = StrSexpVector((packagename, ))
    cls_def = methods_env['getClassDef'](
        StrSexpVector((cls_name,)),
        package=package
    )
    if cls_def is rinterface.NULL:
        raise ValueError(
            f'{cls_name} is not a class in the R package {packagename!r}'
        )
    cls_def = ClassRepresentation(cls_def)
    cls_def.__rname__ = cls_name
    return cls_def


class RS4_Type(abc.ABCMeta):

    def __new__(mcs, name, bases, cls_dict):

        try:
            cls_rname = cls_dict['__rname__']
        except KeyError:
            cls_rname = name

        try:
            accessors = cls_dict['__accessors__']
        except KeyError:
            accessors = []

        for rname, where, \
                python_name, as_property, \
                docstring in accessors:

            if where is None:
                where = rinterface.globalenv
            else:
                where = StrSexpVector(('package:%s' % where, ))

            if python_name is None:
                python_name = rname

            signature = StrSexpVector((cls_rname, ))
            r_meth = getmethod(StrSexpVector((rname, )),
                               signature=signature,
                               where=where)
            r_meth = conversion.get_conversion().rpy2py(r_meth)
            if as_property:
                cls_dict[python_name] = property(r_meth, None, None,
                                                 doc=docstring)
            else:
                cls_dict[python_name] = lambda self: r_meth(self)

        return type.__new__(mcs, name, bases, cls_dict)


# playground to experiment with more metaclass-level automation

class RS4Auto_Type(abc.ABCMeta):
    """ This type (metaclass) takes an R S4 class
    and create a Python class out of it,
    copying the R documention page into the Python docstring.
    A class with this metaclass has the following optional
    attributes: __rname__, __rpackagename__, __attr__translation,
    __meth_translation__.
    """
    def __new__(mcs, name, bases, cls_dict):
        try:
            cls_rname = cls_dict['__rname__']
        except KeyError:
            cls_rname = name

        try:
            cls_rpackagename = cls_dict['__rpackagename__']
        except KeyError:
            cls_rpackagename = None

        try:
            cls_attr_translation = cls_dict['__attr_translation__']
        except KeyError:
            cls_attr_translation = {}
        try:
            cls_meth_translation = cls_dict['__meth_translation__']
        except KeyError:
            cls_meth_translation = {}

        cls_def = getclassdef(cls_rname, cls_rpackagename)

        # documentation / help
        if cls_rpackagename is None:
            cls_dict['__doc__'] = "Undocumented class from the R workspace."
        else:
            pack_help = rhelp.Package(cls_rpackagename)
            page_help = None
            try:
                # R's classes are sometimes documented with a prefix 'class.'
                page_help = pack_help.fetch('%s-class' % cls_def.__rname__)
            except rhelp.HelpNotFoundError:
                pass
            if page_help is None:
                try:
                    page_help = pack_help.fetch(cls_def.__rname__)
                except rhelp.HelpNotFoundError:
                    pass
            if page_help is None:
                cls_dict['__doc__'] = ('Unable to fetch R documentation '
                                       'for the class')
            else:
                cls_dict['__doc__'] = ''.join(page_help.to_docstring())

        for slt_name in cls_def.slots:
            # TODO: sanity check on the slot name
            try:
                slt_name = cls_attr_translation[slt_name]
            except KeyError:
                # no translation: abort
                pass

            # TODO: isolate the slot documentation and have it here
            cls_dict[slt_name] = property(lambda self: self.do_slot(slt_name),
                                          None, None,
                                          None)

        # Now tackle the methods
        all_generics = methods_env['getGenerics']()
        findmethods = methods_env['findMethods']

        # does not seem elegant, but there is probably nothing else to do
        # than loop across all generics
        r_cls_rname = StrSexpVector((cls_rname, ))
        for funcname in all_generics:
            all_methods = findmethods(StrSexpVector((funcname, )),
                                      classes=r_cls_rname)

            # skip if no methods (issue #301). R's findMethods() result
            # does not have an attribute "names" if of length zero.
            if len(all_methods) == 0:
                continue
            # all_methods contains all method/signature pairs
            # having the class we are considering somewhere in the signature
            # (the R/S4 systems allows multiple dispatch)
            for name, meth in zip(all_methods.do_slot("names"), all_methods):
                # R/S4 is storing each method/signature as a string,
                # with the argument type separated by the character '#'
                # We will re-use that name for the Python name
                # (no multiple dispatch in python, the method name
                # will not be enough), replacing the '#'s with '__'s.
                signature = name.split("#")
                meth_name = '__'.join(signature)
                # function names ending with '<-' indicate that the function
                # is a setter of some sort. We reflect that by adding a 'set_'
                # prefix to the Python name (and of course remove the
                # suffix '<-').
                if funcname.endswith('<-'):
                    meth_name = 'set_%s__%s' % (funcname[:-2], meth_name)
                else:
                    meth_name = '%s__%s' % (funcname, meth_name)
                # finally replace remaining '.'s in the Python name with '_'s
                meth_name = meth_name.replace('.', '_')

            # TODO: sanity check on the function name
                try:
                    meth_name = cls_meth_translation[meth_name]
                except KeyError:
                    # no translation: abort
                    pass

            # TODO: isolate the slot documentation and have it here

                if meth_name in cls_dict:
                    raise Exception("Duplicated attribute/method name.")
                cls_dict[meth_name] = meth

        return abc.ABCMeta.__new__(mcs, name, bases, cls_dict)


def set_accessors(cls, cls_name, where, acs):
    # set accessors (to be abandonned for the metaclass above ?)

    if where is None:
        where = rinterface.globalenv
    else:
        where = "package:" + str(where)
        where = StrSexpVector((where, ))

    for r_name, python_name, as_property, docstring in acs:
        if python_name is None:
            python_name = r_name
        r_meth = getmethod(StrSexpVector((r_name, )),
                           signature=StrSexpVector((cls_name, )),
                           where=where)
        r_meth = conversion.get_conversion().rpy2py(r_meth)
        if as_property:
            setattr(cls, python_name, property(r_meth, None, None))
        else:
            setattr(cls, python_name, lambda self: r_meth(self))


def get_classnames(packname):
    res = methods_env['getClasses'](
        where=StrSexpVector(("package:%s" % packname, ))
    )
    return tuple(res)


# Namespace to store the definition of RS4 classes
rs4classes = SimpleNamespace()


def _getclass(rclsname):
    if hasattr(rs4classes, rclsname):
        rcls = getattr(rs4classes, rclsname)
    else:
        # dynamically create a class
        rcls = type(rclsname,
                    (RS4, ),
                    dict())
        setattr(rs4classes,
                rclsname,
                rcls)
    return rcls


def rs4instance_factory(robj):
    """
    Return an RS4 objects (R objects in the 'S4' class system)
    as a Python object of type inheriting from `robjects.methods.RS4`.

    The types are located in the namespace `robjects.methods.rs4classes`,
    and a dummy type is dynamically created whenever necessary.
    """
    clslist = None
    if len(robj.rclass) > 1:
        raise ValueError(
            'Currently unable to handle more than one class per object'
        )
    for rclsname in robj.rclass:
        rcls = _getclass(rclsname)
        return rcls(robj)
    if clslist is None:
        return robj


methods_env = rinterface.baseenv.find('as.environment')(
    StrSexpVector(('package:methods', ))
)
