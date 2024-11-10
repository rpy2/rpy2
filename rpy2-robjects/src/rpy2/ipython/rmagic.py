# -*- coding: utf-8 -*-
"""
======
Rmagic
======

Magic command interface for interactive work with R in ipython. %R and %%R are
the line and cell magics, respectively.

.. note::

  You will need a working copy of R.

Usage
=====

To enable the magics below, execute `%load_ext rpy2.ipython`.

`%R`

{R_DOC}

`%Rpush`

{RPUSH_DOC}

`%Rpull`

{RPULL_DOC}

`%Rget`

{RGET_DOC}

"""

# -----------------------------------------------------------------------------
#  Copyright (C) 2012 The IPython Development Team
#  Copyright (C) 2013-2019 rpy2 authors
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
# -----------------------------------------------------------------------------

import contextlib
import sys
import tempfile
from glob import glob
import os
from shutil import rmtree
import textwrap
import typing

import rpy2.rinterface_lib.callbacks

import rpy2.rinterface as ri

import rpy2.rinterface_lib.openrlib
import rpy2.robjects as ro
import rpy2.robjects.packages as rpacks
from rpy2.robjects.lib import grdevices
from rpy2.robjects.conversion import (Converter,
                                      localconverter,
                                      get_conversion)
import warnings

# Try loading pandas and numpy, emitting a warning if either cannot be
# loaded.
try:
    import numpy  # noqa: F401
    NUMPY_IMPORTED = True
    try:
        import pandas  # noqa: F401
        PANDAS_IMPORTED = True
    except ImportError as ie:
        PANDAS_IMPORTED = False
        warnings.warn('The Python package `pandas` is strongly '
                      'recommended when using `rpy2.ipython`. '
                      'Unfortunately it could not be loaded '
                      '(error: %s), '
                      'but at least we found `numpy`.' % str(ie))
except ImportError as ie:
    NUMPY_IMPORTED = False
    PANDAS_IMPORTED = False
    warnings.warn('The Python package `pandas` is strongly '
                  'recommended when using `rpy2.ipython`. '
                  'Unfortunately it could not be loaded, '
                  'as we did not manage to load `numpy` '
                  'in the first place (error: %s).' % str(ie))

# IPython imports.

import IPython.display  # type: ignore
from IPython.core import displaypub  # type: ignore
from IPython.core.magic import (Magics,   # type: ignore
                                magics_class,
                                line_cell_magic,
                                line_magic,
                                needs_local_scope,
                                no_var_expand)
from IPython.core.magic_arguments import (argument,  # type: ignore
                                          argument_group,
                                          magic_arguments,
                                          parse_argstring)

template_converter = get_conversion()

DEVICES_STATIC_RASTER: typing.Set[str] = {'png', 'jpeg'}
DEVICES_STATIC = DEVICES_STATIC_RASTER | {'svg'}
DEVICES_SUPPORTED = DEVICES_STATIC | {'X11'}


if NUMPY_IMPORTED:
    if PANDAS_IMPORTED:
        def _get_ipython_template_converter(template_converter=template_converter):
            from rpy2.robjects import numpy2ri
            template_converter += numpy2ri.converter
            from rpy2.robjects import pandas2ri
            template_converter += pandas2ri.converter
            return template_converter
    else:
        def _get_ipython_template_converter(template_converter=template_converter):
            from rpy2.robjects import numpy2ri
            template_converter += numpy2ri.converter
            return template_converter
else:
    def _get_ipython_template_converter(template_converter=template_converter):
        return template_converter


def _get_converter(template_converter=template_converter):
    return Converter('ipython conversion',
                     template=template_converter)


ipy_template_converter = _get_ipython_template_converter(template_converter)
converter = _get_converter(template_converter=ipy_template_converter)


def CELL_DISPLAY_DEFAULT(res, args):
    return ro.r.show(res)


class RInterpreterError(ri.embedded.RRuntimeError):
    """An error when running R code in a %%R magic cell."""

    msg_prefix_template = ('Failed to parse and evaluate line %r.\n'
                           'R error message: %r')
    rstdout_prefix = '\nR stdout:\n'

    def __init__(self, line, err, stdout):
        self.line = line
        self.err = err.rstrip()
        self.stdout = stdout.rstrip()

    def __str__(self):
        s = (self.msg_prefix_template %
             (self.line, self.err))
        if self.stdout and (self.stdout != self.err):
            s += self.rstdout_prefix + self.stdout
        return s


# The default conversion for lists is currently to make them an R list. That
# has some advantages, but can be inconvenient (and, it's inconsistent with
# the way python lists are automatically converted by numpy functions), so
# for interactive use in the rmagic, we call unlist, which converts lists to
# vectors **if the list was of uniform (atomic) type**.
@converter.py2rpy.register(list)
def py2rpy_list(obj):
    # simplify2array is a utility function, but nice for us
    # TODO: use an early binding of the R function
    cv = ro.conversion.get_conversion()
    robj = ri.ListSexpVector(
            [cv.py2rpy(x) for x in obj]
        )
    res = ro.r.simplify2array(robj)
    # The current default converter for the ipython rmagic
    # might make `res` a numpy array. We need to ensure that
    # a rpy2 objects is returned (issue #866).
    res_rpy = cv.py2rpy(res)
    return res_rpy


def _find(name: str, ns: dict):
    """Find a Python name, which might include dot-separated path to a name.

    Args:
    - name: a key in dict if no dot ('.') in it, otherwise
    a sequence of dot-separated namespaces with the name of the
    object last (e.g., `package.module.name`).
    Returns:
    The object wanted. Raises a NameError or an AttributeError if not found.
    """

    obj = None
    obj_path = name.split('.')
    look_for_i = 0
    try:
        obj = ns[obj_path[look_for_i]]
    except KeyError as e:
        message = f"name '{obj_path[look_for_i]}' is not defined."
        if obj_path[look_for_i] == "":
            message += ' Did you forget to remove trailing comma `,` or included spaces?'
        raise NameError(message) from e
    look_for_i += 1
    while look_for_i < len(obj_path):
        try:
            obj = getattr(obj, obj_path[look_for_i])
        except AttributeError as e:
            raise AttributeError(
                f"'{'.'.join(obj_path[:look_for_i])}' "
                f"has no attribute '{obj_path[look_for_i]}'."
            ) from e
        look_for_i += 1
    return obj


def _parse_input_argument(arg: str) -> typing.Tuple[str, str]:
    """Process the input to an R magic commmand (`%R`, `%%R`, `%Rpush`)."""
    arg_elts = arg.split('=', maxsplit=1)
    if len(arg_elts) == 1:
        rhs = arg_elts[0]
        lhs = rhs
    else:
        lhs, rhs = arg_elts
    return lhs, rhs


# TODO: remove ?
# # The R magic is opiniated about what the R vectors should become.
# @converter.ri2ro.register(ri.SexpVector)
# def _(obj):
#     if 'data.frame' in obj.rclass:
#         # request to turn it to a pandas DataFrame
#         res = converter.rpy2py(obj)
#     else:
#         res = ro.sexpvector_to_ro(obj)
#     return res


def display_figures(graph_dir, format='png'):
    """Iterator to display PNG figures generated by R.

    graph_dir : str
        A directory where R figures are to be searched.

    The iterator yields the image objects."""

    assert format in DEVICES_STATIC_RASTER
    for imgfile in sorted(glob(os.path.join(graph_dir, f'Rplots*{format}'))):
        if os.stat(imgfile).st_size >= 1000:
            img = IPython.display.Image(filename=imgfile)
            IPython.display.display(img,
                                    metadata={})
            # TODO: Synchronization in the console (though it's a bandaid, not a
            # real solution).
            sys.stdout.flush()
            sys.stderr.flush()
            yield img


def display_figures_svg(graph_dir, isolate_svgs=True):
    """Display SVG figures generated by R.

    graph_dir : str
        A directory where R figures are to be searched.
    isolate_svgs : bool
        Enable SVG namespace isolation in metadata.

    The iterator yields the image object."""

    # as onefile=TRUE, there is only one .svg file
    imgfile = "%s/Rplot.svg" % graph_dir
    # Cairo creates an SVG file every time R is called
    # -- empty ones are not published
    if os.stat(imgfile).st_size >= 1000:
        img = IPython.display.SVG(filename=imgfile)
        IPython.display.display_svg(
            img,
            metadata={'image/svg+xml': dict(isolated=True)} if isolate_svgs else {}
        )
        # TODO: Synchronization in the console (though it's a bandaid, not a
        # real solution).
        sys.stdout.flush()
        sys.stderr.flush()
        yield img


@magics_class
class RMagics(Magics):
    """A set of magics useful for interactive work with R via rpy2.
    """

    def __init__(self, shell, converter=converter,
                 cache_display_data=False, device='png'):
        """
        Parameters
        ----------

        shell : IPython shell

        converter : rpy2 Converter instance to use. If None,
                    the magic's current converter is used.

        cache_display_data : bool
            If True, the published results of the final call to R are
            cached in the variable 'display_cache'.

        device : ['png', 'jpeg', 'X11', 'svg']
            Device to be used for plotting.
            Currently only 'png', 'jpeg', 'X11' and 'svg' are supported,
            with 'X11' allowing interactive plots on a locally-running jupyter,
            and the other allowing to visualize R figure generated on a remote
            jupyter server/kernel.
        """
        super(RMagics, self).__init__(shell)
        self.cache_display_data = cache_display_data
        self.Rstdout_cache = []
        self.converter = converter
        self.set_R_plotting_device(device)

    def set_R_plotting_device(self, device):
        """
        Set which device R should use to produce plots.
        If device == 'svg' then the package 'Cairo'
        must be installed. Because Cairo forces "onefile=TRUE",
        it is not posible to include multiple plots per cell.

        :param device: ['png', 'jpeg', 'X11', 'svg']
            Device to be used for plotting.
            Currently only 'png', 'jpeg', 'X11' and 'svg' are supported,
            with 'X11' allowing interactive plots on a locally-running jupyter,
            and the other allowing to visualize R figure generated on a remote
            jupyter server/kernel.
        """
        device = device.strip()
        if device not in DEVICES_SUPPORTED:
            raise ValueError(
                f'device must be one of {DEVICES_SUPPORTED}, got "{device}"'
            )
        if device == 'svg':
            try:
                self.cairo = rpacks.importr('Cairo')
            except ri.embedded.RRuntimeError as rre:
                if rpacks.isinstalled('Cairo'):
                    msg = ('An error occurred when trying to load the ' +
                           'R package Cairo\'\n%s' % str(rre))
                else:
                    msg = textwrap.dedent("""
                    The R package 'Cairo' is required but it does not appear
                    to be installed/available. Try:

                    import rpy2.robjects.packages as rpacks
                    utils = rpacks.importr('utils')
                    utils.chooseCRANmirror(ind=1)
                    utils.install_packages('Cairo')
                    """)
                raise RInterpreterError(msg)
        self.device = device

    @line_magic
    def Rdevice(self, line):
        """
        Change the plotting device R uses to one of {}.
        """.format(DEVICES_SUPPORTED)
        self.set_R_plotting_device(line.strip())

    def eval(self, code):
        """
        Parse and evaluate a line of R code with rpy2.
        Returns the output to R's stdout() connection,
        the value generated by evaluating the code, and a
        boolean indicating whether the return value would be
        visible if the line of code were evaluated in an R REPL.

        R Code evaluation and visibility determination are done via an R call
        of the form withVisible(code_string), and this entire expression needs
        to be evaluated in R (we can't use rpy2 function proxies here, as
        withVisible is a LISPy R function).
        """
        with contextlib.ExitStack() as stack:
            obj_in_module = (rpy2.rinterface_lib
                             .callbacks.obj_in_module)
            if self.cache_display_data:
                stack.enter_context(
                    obj_in_module(
                        rpy2.rinterface_lib.callbacks,
                        'consolewrite_print',
                        self.write_console_regular
                    )
                )
            stack.enter_context(
                obj_in_module(rpy2.rinterface_lib.callbacks,
                              'consolewrite_warnerror',
                              self.write_console_regular)
            )
            stack.enter_context(
                obj_in_module(
                    rpy2.rinterface_lib.callbacks,
                    '_WRITECONSOLE_EXCEPTION_LOG',
                    '%s')
            )
            try:
                # Need the newline in case the last line in code is a comment.
                r_expr = ri.parse(code)
                value, visible = ri.evalr_expr_with_visible(
                    r_expr
                )
            except (ri.embedded.RRuntimeError, ValueError) as exception:
                # Otherwise next return seems to have copy of error.
                warning_or_other_msg = self.flush()
                raise RInterpreterError(code, str(exception),
                                        warning_or_other_msg)
            finally:
                ro._print_deferred_warnings()
            text_output = self.flush()
            return text_output, value, visible[0]

    def write_console_regular(self, output):
        """
        A hook to capture R's stdout in a cache.
        """
        self.Rstdout_cache.append(output)

    def flush(self):
        """
        Flush R's stdout cache to a string, returning the string.
        """
        value = ''.join(self.Rstdout_cache)
        self.Rstdout_cache = []
        return value

    def _import_name_into_r(
            self, arg: str, env: ri.SexpEnvironment,
            local_ns: dict
    ) -> None:
        lhs, rhs = _parse_input_argument(arg)
        val = None
        try:
            val = _find(rhs, local_ns)
        except NameError:
            if self.shell is None:
                warnings.warn(
                    f'The shell is None. Unable to look for {rhs}.'
                )
            else:
                val = _find(rhs, self.shell.user_ns)
        if val is not None:
            env[lhs] = val

    def _find_converter(
            self, name: str, local_ns: dict
    ) -> ro.conversion.Converter:
        converter = None
        if name is None:
            converter = self.converter
        else:
            try:
                converter = _find(name, local_ns)
            except NameError:
                if self.shell is None:
                    warnings.warn(
                        f'The shell is None. Unable to look for converter {name}.'
                    )
                else:
                    converter = _find(name, self.shell.user_ns)

        if not isinstance(converter, Converter):
            raise TypeError("'%s' must be a %s object (but it is a %s)."
                            % (converter, Converter,
                               type(converter)))
        return converter

    # @skip_doctest
    @magic_arguments()
    @argument(
        '-c', '--converter',
        default=None,
        help=textwrap.dedent("""
        Name of local converter to use. A converter contains the rules to
        convert objects back and forth between Python and R. If not
        specified/None, the defaut converter for the magic\'s module is used
        (that is rpy2\'s default converter + numpy converter + pandas converter
        if all three are available)."""))
    @argument(
        'inputs',
        nargs='*',
        )
    @needs_local_scope
    @line_magic
    def Rpush(self, line, local_ns=None):
        """
        A line-level magic that pushes
        variables from python to R. The line should be made up
        of whitespace separated variable names in the IPython
        namespace::

            In [7]: import numpy as np

            In [8]: X = np.array([4.5,6.3,7.9])

            In [9]: X.mean()
            Out[9]: 6.2333333333333343

            In [10]: %Rpush X

            In [11]: %R mean(X)
            Out[11]: array([ 6.23333333])

        """
        args = parse_argstring(self.Rpush, line)

        converter = self._find_converter(args.converter, local_ns)

        if local_ns is None:
            local_ns = {}

        with localconverter(converter):
            for arg in args.inputs:
                self._import_name_into_r(arg, ro.globalenv, local_ns)

    # @skip_doctest
    @magic_arguments()
    @argument(
        'outputs',
        nargs='*',
        )
    @line_magic
    def Rpull(self, line):
        """
        A line-level magic for R that pulls
        variables from python to rpy2::

            In [18]: _ = %R x = c(3,4,6.7); y = c(4,6,7); z = c('a',3,4)

            In [19]: %Rpull x  y z

            In [20]: x
            Out[20]: array([ 3. ,  4. ,  6.7])

            In [21]: y
            Out[21]: array([ 4.,  6.,  7.])

            In [22]: z
            Out[22]:
            array(['a', '3', '4'],
                  dtype='|S1')


        This is useful when a structured array is desired as output, or
        when the object in R has mixed data types.
        See the %%R docstring for more examples.

        Notes
        -----

        Beware that R names can have dots ('.') so this is not fool proof.
        To avoid this, don't name your R objects with dots...

        """
        args = parse_argstring(self.Rpull, line)
        outputs = args.outputs
        with localconverter(self.converter):
            for output in outputs:
                robj = ri.globalenv.find(output)
                self.shell.push({output: robj})

    # @skip_doctest
    @magic_arguments()
    @argument(
        'output',
        nargs=1,
        type=str,
        )
    @line_magic
    def Rget(self, line):
        """
        Return an object from rpy2, possibly as a structured array (if
        possible).
        Similar to Rpull except only one argument is accepted and the value is
        returned rather than pushed to self.shell.user_ns::

            In [3]: dtype=[('x', '<i4'), ('y', '<f8'), ('z', '|S1')]

            In [4]: datapy = np.array([(1, 2.9, 'a'), (2, 3.5, 'b'),
            ...                        (3, 2.1, 'c'), (4, 5, 'e')],
            ...                        dtype=dtype)

            In [5]: %R -i datapy

            In [6]: %Rget datapy
            Out[6]:
            array([['1', '2', '3', '4'],
                   ['2', '3', '2', '5'],
                   ['a', 'b', 'c', 'e']],
                  dtype='|S1')
        """
        args = parse_argstring(self.Rget, line)
        output = args.output
        # get the R object with the given name, starting from globalenv
        # in the search path
        with localconverter(self.converter):
            res = ro.globalenv.find(output[0])
        return res

    def setup_graphics(self, args):
        """Setup graphics in preparation for evaluating R code.

        args : argparse bunch (should be whatever the R magic got)."""

        if getattr(args, 'units') is not None:
            if args.units != "px" and getattr(args, 'res') is None:
                args.res = 72

        plot_arg_names = ['width', 'height', 'pointsize', 'bg', 'type']
        if self.device in DEVICES_STATIC_RASTER:
            plot_arg_names += ['units', 'res']

        argdict = {}
        for name in plot_arg_names:
            val = getattr(args, name)
            if val is not None:
                argdict[name] = val

        tmpd = None
        if self.device in DEVICES_STATIC:
            # Create a temporary directory for R graphics output
            # TODO: Do we want to capture file output for other device types
            # other than svg & png?
            tmpd = tempfile.mkdtemp()
            tmpd_fix_slashes = tmpd.replace('\\', '/')

            if self.device in DEVICES_STATIC_RASTER:
                # Note: that %% is to pass into R for interpolation there.
                rfunc = getattr(grdevices, self.device)
                rfunc(f'{tmpd_fix_slashes}/Rplots%%03d.{self.device}',
                      **argdict)
            elif self.device == 'svg':
                self.cairo.CairoSVG(f'{tmpd_fix_slashes}/Rplot.svg',
                                    **argdict)

        elif self.device == 'X11':
            # Open a new X11 device, except if the current one is already an
            # X11 device.
            ro.r("""
            if (substr(names(dev.cur()), 1, 3) != "X11") {
                X11()
            }""")

        else:
            # TODO: This isn't actually an R interpreter error...
            raise RInterpreterError(
                f'device must be one of {DEVICES_SUPPORTED}')

        return tmpd

    def publish_graphics(self, graph_dir, isolate_svgs=True):
        """Wrap graphic file data for presentation in IPython.

        This method is deprecated. Use `display_figures` or
        'display_figures_svg` instead.

        graph_dir : str
            Probably provided by some tmpdir call
        isolate_svgs : bool
            Enable SVG namespace isolation in metadata"""

        warnings.warn('Use method fetch_figures.', DeprecationWarning)
        # read in all the saved image files
        images = []
        display_data = []

        # Default empty metadata dictionary.
        md = {}

        if self.device == 'png':
            for imgfile in sorted(glob('%s/Rplots*png' % graph_dir)):
                if os.stat(imgfile).st_size >= 1000:
                    with open(imgfile, 'rb') as fh_img:
                        images.append(fh_img.read())
        else:
            # as onefile=TRUE, there is only one .svg file
            imgfile = "%s/Rplot.svg" % graph_dir
            # Cairo creates an SVG file every time R is called
            # -- empty ones are not published
            if os.stat(imgfile).st_size >= 1000:
                with open(imgfile, 'rb') as fh_img:
                    images.append(fh_img.read().decode())

        mimetypes = {'png': 'image/png', 'svg': 'image/svg+xml'}
        mime = mimetypes[self.device]

        # By default, isolate SVG images in the Notebook to avoid garbling.
        if images and self.device == "svg" and isolate_svgs:
            md = {'image/svg+xml': dict(isolated=True)}

        # Flush text streams before sending figures, helps a little with
        # output.
        for image in images:
            # TODO: Synchronization in the console (though it's a bandaid, not a
            # real solution).
            sys.stdout.flush()
            sys.stderr.flush()
            display_data.append(('RMagic.R', {mime: image}))

        return display_data, md

    # @skip_doctest
    @magic_arguments()
    @argument(
        '-i', '--input', action='append',
        help=textwrap.dedent("""
        Names of Python objects to be assigned to R
        objects after using the default converter or
        one specified through the argument `-c/--converter`.
        Multiple inputs can be passed separated only by commas with no
        whitespace.

        Names of Python objects can be either the name of an object
        in the current notebook/ipython shell, or a path to a name
        nested in a namespace visible from the current notebook/ipython
        shell. For example, '-i myvariable' or
        '-i mypackage.myothervariable' would both work.

        Each input can be either the name of Python object, in which
        case the same name will be used for the R object, or an
        expression of the form <r-name>=<python-name>.""")
    )
    @argument(
        '-o', '--output', action='append',
        help=textwrap.dedent("""
        Names of variables to be pushed from rpy2 to `shell.user_ns` after
        executing cell body (rpy2's internal facilities will apply ri2ro as
        appropriate). Multiple names can be passed separated only by commas
        with no whitespace.""")
    )
    @argument(
        '-n', '--noreturn',
        help='Force the magic to not return anything.',
        action='store_true',
        default=False
        )
    @argument_group("Plot", "Arguments to plotting device")
    @argument(
        '-w', '--width', type=float,
        help='Width of plotting device in R.'
        )
    @argument(
        '-h', '--height', type=float,
        help='Height of plotting device in R.'
        )
    @argument(
        '-p', '--pointsize', type=int,
        help='Pointsize of plotting device in R.'
        )
    @argument(
        '-b', '--bg',
        help='Background of plotting device in R.'
        )
    @argument_group("SVG", "SVG specific arguments")
    @argument(
        '--noisolation',
        help=textwrap.dedent("""
        Disable SVG isolation in the Notebook. By default, SVGs are isolated to
        avoid namespace collisions between figures. Disabling SVG isolation
        allows to reference previous figures or share CSS rules across a set
        of SVGs."""),
        action='store_false',
        default=True,
        dest='isolate_svgs'
        )
    @argument_group("PNG", "PNG specific arguments")
    @argument(
        '-u', '--units', type=str, choices=["px", "in", "cm", "mm"],
        help=textwrap.dedent("""
        Units of png plotting device sent as an argument to *png* in R. One of
        ["px", "in", "cm", "mm"]."""))
    @argument(
        '-r', '--res', type=int,
        help=textwrap.dedent("""
        Resolution of png plotting device sent as an argument to *png* in R.
        Defaults to 72 if *units* is one of ["in", "cm", "mm"].""")
        )
    @argument(
        '--type', type=str,
        choices=['cairo', 'cairo-png', 'Xlib', 'quartz'],
        help=textwrap.dedent("""
        Type device used to generate the figure.
        """))
    @argument(
        '-c', '--converter',
        default=None,
        help=textwrap.dedent("""
        Name of local converter to use. A converter contains the rules to
        convert objects back and forth between Python and R. If not
        specified/None, the defaut converter for the magic\'s module is used
        (that is rpy2\'s default converter + numpy converter + pandas converter
        if all three are available)."""))
    @argument(
        '-d', '--display',
        default=None,
        help=textwrap.dedent("""
        Name of function to use to display the output of an R cell (the last
        object or function call that does not have a left-hand side
        assignment). That function will have the signature `(robject, args)`
        where `robject` is the R objects that is an output of the cell, and
        `args` a namespace with all parameters passed to the cell.
        """))
    @argument(
        'code',
        nargs='*',
        )
    @needs_local_scope
    @line_cell_magic
    @no_var_expand
    def R(self, line, cell=None, local_ns=None):
        """
        Execute code in R, optionally returning results to the Python runtime.

        In line mode, this will evaluate an expression and convert the returned
        value to a Python object.  The return value is determined by rpy2's
        behaviour of returning the result of evaluating the final expression.

        Multiple R expressions can be executed by joining them with
        semicolons::

            In [9]: %R X=c(1,4,5,7); sd(X); mean(X)
            Out[9]: array([ 4.25])

        In cell mode, this will run a block of R code. The resulting value
        is printed if it would be printed when evaluating the same code
        within a standard R REPL.

        Nothing is returned to python by default in cell mode::

            In [10]: %%R
               ....: Y = c(2,4,3,9)
               ....: summary(lm(Y~X))

            Call:
            lm(formula = Y ~ X)

            Residuals:
                1     2     3     4
             0.88 -0.24 -2.28  1.64

            Coefficients:
                        Estimate Std. Error t value Pr(>|t|)
            (Intercept)   0.0800     2.3000   0.035    0.975
            X             1.0400     0.4822   2.157    0.164

            Residual standard error: 2.088 on 2 degrees of freedom
            Multiple R-squared: 0.6993,Adjusted R-squared: 0.549
            F-statistic: 4.651 on 1 and 2 DF,  p-value: 0.1638

        In the notebook, plots are published as the output of the cell::

            %R plot(X, Y)

        will create a scatter plot of X bs Y.

        If cell is not None and line has some R code, it is prepended to
        the R code in cell.

        Objects can be passed back and forth between rpy2 and python via the
        -i -o flags in line::

            In [14]: Z = np.array([1,4,5,10])

            In [15]: %R -i Z mean(Z)
            Out[15]: array([ 5.])


            In [16]: %R -o W W=Z*mean(Z)
            Out[16]: array([  5.,  20.,  25.,  50.])

            In [17]: W
            Out[17]: array([  5.,  20.,  25.,  50.])

        The return value is determined by these rules:

        * If the cell is not None (i.e., has contents), the magic returns None.

        * If the final line results in a NULL value when evaluated
          by rpy2, then None is returned.

        * No attempt is made to convert the final value to a structured array.
          Use %Rget to push a structured array.

        * If the -n flag is present, there is no return value.

        * A trailing ';' will also result in no return value as the last
          value in the line is an empty string.
        """

        args = parse_argstring(self.R, line)

        # arguments 'code' in line are prepended to
        # the cell lines

        if cell is None:
            code = ''
            return_output = True
            line_mode = True
        else:
            code = cell
            return_output = False
            line_mode = False

        code = ' '.join(args.code) + code

        # if there is no local namespace then default to an empty dict
        if local_ns is None:
            local_ns = {}

        converter = self._find_converter(args.converter, local_ns)

        if args.input:
            with localconverter(converter) as cv:
                for arg in ','.join(args.input).split(','):
                    self._import_name_into_r(arg, ro.globalenv, local_ns)

        if args.display:
            try:
                cell_display = local_ns[args.display]
            except KeyError:
                try:
                    cell_display = self.shell.user_ns[args.display]
                except KeyError:
                    raise NameError("name '%s' is not defined" % args.display)
        else:
            cell_display = CELL_DISPLAY_DEFAULT

        tmpd = self.setup_graphics(args)

        text_output = ''
        display_data = []
        try:
            if line_mode:
                for line in code.split(';'):
                    text_result, result, visible = self.eval(line)
                    text_output += text_result
                if text_result:
                    # The last line printed something to the console so
                    # we won't return it.
                    return_output = False
            else:
                text_result, result, visible = self.eval(code)
                text_output += text_result
                if visible:
                    with contextlib.ExitStack() as stack:
                        obj_in_module = (rpy2.rinterface_lib
                                         .callbacks
                                         .obj_in_module)
                        if self.cache_display_data:
                            stack.enter_context(
                                obj_in_module(rpy2.rinterface_lib
                                              .callbacks,
                                              'consolewrite_print',
                                              self.write_console_regular)
                            )
                        stack.enter_context(
                            obj_in_module(
                                rpy2.rinterface_lib.callbacks,
                                'consolewrite_warnerror',
                                self.write_console_regular
                            )
                        )
                        stack.enter_context(
                            obj_in_module(
                                rpy2.rinterface_lib.callbacks,
                                '_WRITECONSOLE_EXCEPTION_LOG',
                                '%s')
                        )
                        cell_display(result, args)
                        text_output += self.flush()

        except RInterpreterError as e:
            # TODO: Maybe we should make this red or something?
            print(e.stdout)
            if not e.stdout.endswith(e.err):
                print(e.err)
            raise e
        finally:
            if self.device in DEVICES_STATIC:
                ro.r('dev.off()')
            if text_output:
                # display_data.append(('RMagic.R', {'text/plain':text_output}))
                displaypub.publish_display_data(
                    source='RMagic.R',
                    data={'text/plain': text_output})
            # publish figures generated by R.
            if self.device in DEVICES_STATIC_RASTER:
                for _ in display_figures(tmpd, format=self.device):
                    if self.cache_display_data:
                        display_data.append(_)
            elif self.device == 'svg':
                for _ in display_figures_svg(tmpd):
                    if self.cache_display_data:
                        display_data.append(_)

            # kill the temporary directory - currently created only for "svg"
            # and ("png"|"jpeg") (else it's None).
            if tmpd:
                rmtree(tmpd)

        if args.output:
            with localconverter(converter) as cv:
                for output in ','.join(args.output).split(','):
                    output_ipy = ro.globalenv.find(output)
                    self.shell.push({output: output_ipy})

        # this will keep a reference to the display_data
        # which might be useful to other objects who happen to use
        # this method

        if self.cache_display_data:
            self.display_cache = display_data

        # We're in line mode and return_output is still True,
        # so return the converted result
        if return_output and not args.noreturn:
            if result is not ri.NULL:
                with localconverter(converter) as cv:
                    res = cv.rpy2py(result)
                return res


__doc__ = __doc__.format(
                R_DOC='{0}{1}'.format(' '*8, RMagics.R.__doc__),
                RPUSH_DOC='{0}{1}'.format(' '*8, RMagics.Rpush.__doc__),
                RPULL_DOC='{0}{1}'.format(' '*8, RMagics.Rpull.__doc__),
                RGET_DOC='{0}{1}'.format(' '*8, RMagics.Rget.__doc__)
)


def load_ipython_extension(ip):
    """Load the extension in IPython."""

    ip.register_magics(RMagics)