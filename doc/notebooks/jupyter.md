```python
from functools import partial
from rpy2.ipython import html
html.html_rdataframe=partial(html.html_rdataframe, table_class="docutils")
```

# Data Import

We choose to use an external dataset to demonstrate how R's own data import
features can be used.

```python
from rpy2.robjects.packages import importr
utils = importr('utils')

dataf = utils.read_csv('https://raw.githubusercontent.com/jakevdp/PythonDataScienceHandbook/'
                       'master/notebooks_v1/data/california_cities.csv')
```

The objects returned by R's own `read.csv()` function (note that the R function
in the R package `utils` is called `read.csv()` while the Python function is called
`read_csv()` - `rpy2` converts R symbols with dots to underscores for Python).

`rpy2` provides customization to display R objects such as data frames in HTML
in a notebook. That customization is enabled as follows:

```python
import rpy2.ipython.html
rpy2.ipython.html.init_printing()
```

```python
dataf
```

```python
dataf.colnames
```

```python
stats = importr('stats')
base = importr('base')
fit = stats.lm('elevation_m ~ latd + longd', data=dataf)
fit
```

# Graphics

R has arguably some the best static visualizations, often looking more polished
than other visualization systems and this without the need to spend much
effort on them.

## Using `ggplot2`

Among R visulization pacakges, `ggplot2` has emerged as something Python users
wished so much they had that various projects to try port it to Python
are regularly started.

However, the best way to have `ggplot2` might be to use `ggplot2` from Python.

```python
import rpy2.robjects.lib.ggplot2 as gp
```


R lets is function parameters be unevaluated language objects, which is fairly different
from Python's immediate evaluation. `rpy2` has a utility code to create such R language
objects from Python strings.
It can then become very easy to mix Python and R, with R like a domain-specific language
used from Python.

```python
from rpy2.robjects import rl
```

Calling `ggplot2` looks pretty much like it would in R, which allows one to use the
all available documentation and examples available for the R package. Remember that
this is not a reimplementation of ggplot2 with inevitable differences and delay
for having the latest changes: the R package itself is generating the figures.

```python
p = (gp.ggplot(dataf) +
     gp.aes(x=rl('longd'),
            y=rl('latd'),
            color=rl('population_total'),
            size=rl('area_total_km2')) +
     gp.geom_point() +
     gp.scale_color_continuous(trans='log10'))
```

Plotting the resulting R/ggplot2 object into the output cell of a notebook, is just
function call away.

```python
from rpy2.ipython.ggplot import image_png
image_png(p)
```

All features from `ggplot2` should be present. A more complex example to
get the figure we want is:

```python
from rpy2.robjects.vectors import IntVector
p = (gp.ggplot(dataf) +
     gp.aes(x=rl('longd'),
            y=rl('latd'),
            color=rl('population_total'),
            size=rl('area_total_km2')) +
     gp.geom_point(alpha=0.5) +
     # Axis definitions.
     gp.scale_x_continuous('Longitude') +
     gp.scale_y_continuous('Latitude') +
     # Custom size range.
     gp.scale_size(range=IntVector([1, 18])) +
     # Transform for pop -> color mapping
     gp.scale_color_continuous(trans='log10') +
     # Title.
     gp.ggtitle('California Cities: Area and Population') +
     # Plot theme and text size.
     gp.theme_light(base_size=16))
image_png(p)
```

## Using `ggplot2` extensions

There existing additional R packages extending `ggplot2`, and while it would be impossible
for the rpy2 to provide wrapper for all of them the wrapper for `ggplot2` is based
on class hierarchies that should make the use of such extensions really easy.

For example, to use the viridis color scale, we just need to import the corresponding R package,
and write 3 lines of Python to extend `rpy2`'s ggplot2 wrapper with a new color scale. A clas
diagram with the classes in the rpy2 wrapper for ggplot2 is available in the rpy2 documentation.

```python
viridis = importr('viridis')
class ScaleColorViridis(gp.ScaleColour):
    _constructor = viridis.scale_color_viridis
scale_color_viridis = ScaleColorViridis.new
```

That new color scale can then be used as any other scale already present in `ggplot2`:

```python
p = (gp.ggplot(dataf) +
     gp.aes(x=rl('longd'),
            y=rl('latd'),
            color=rl('population_total'),
            size=rl('area_total_km2')) +
     gp.geom_point(alpha=0.5) +
     gp.scale_x_continuous('Longitude') +
     gp.scale_y_continuous('Latitude') +
     gp.scale_size(range=IntVector([1, 18])) +
     scale_color_viridis(trans='log10') +
     gp.ggtitle('California Cities: Area and Population') +
     gp.theme_light(base_size=16))
image_png(p)
```

# R "magics"

So far we have shown that using `ggplot2` can be done from Python as if it
was just an other Python library for visualization, but R can also be used
in cells.

First the so-called "R magic" extensions should be loaded.

```python
%load_ext rpy2.ipython
```

From now on, code cells starting with `%%R` will see their content evaluated as R code.
If the R code is generating figures, they will be displayed along with the rest of the output.

```python
%%R
R.version.string
```


```python
%%R -i dataf

require(dplyr)
glimpse(dataf)
```

The data frame called `dataf` in our Python notebook was already bound to the name
`dataf` in the R main namespace (`GlobalEnv` in the R lingo) in our previous cell.
We can just use it in subsequent cells.

```python
%%R -w 800 --type=cairo

cat("Running an R code cell.\n")

p <- ggplot(dataf) +
     aes(x=longd,
         y=latd,
         color=population_total,
         size=area_total_km2) +
     geom_point(alpha=0.5) +
     scale_x_continuous('Longitude') +
     scale_y_continuous('Latitude') +
     scale_size(range=c(1, 18)) +
     scale_color_viridis(trans='log10') +
     ggtitle('California Cities: Area and Population') +
     theme_light(base_size=16)
print(p)
```

## Options.

The R "magics" use a number of configurable options that control
aspects of the interaction between Python and R, or between ipython / jupyter
and R. Some of the options can specified through arguments to "magics",
but it is also possible to configure the default value for some of them
when an argument to a "magic" does not specify otherwise. The easiest
way to list these default-configurable options can be achieved
with a "magic":

```python
%Roptions show
```

Changing these defaults requires to modify components of the attribute
:attr:`rpy2.ipython.rmagic.RMagic.options`. Here is an example showing
how to changing the default of R figures rendered in the notebook to "svg".

```python
import IPython
ipy = IPython.get_ipython()
ipy.magics_manager.registry['RMagics'].options.graphics_device_name = 'svg'
```

Another example is how to change conversion rules, that can be
an expensive operation depending object sizes and rules, to a no-op:
no convertion rules to keep all rpy2 objects as proxy wrappers
to R objects for example, no conversion of Python objects to R:

```python
import rpy2.robjects
import IPython
ipy = IPython.get_ipython()

noop_conv = rpy2.robjects.conversion.Converter('No-Op')
noop_conv.rpy2py.register(rpy2.robjects.RObject,
                          rpy2.robjects._rpy2py_robject)

ipy.magics_manager.registry['RMagics'].options.converter = noop_conv
```

Modifying this come with risks though, or afterthoughts about changes made.
While there are some checks in place, the new default options set this way
may break the R "magics".
To address this, options can be restore to
"factory settings". Here again, there is no guarantee that this can work no
matter what. A driven
(or unlucky) user may break this mechanism if modifying it in the module.
Restarting kernel will be needed in that case.

```python
%Roptions refresh
```

## Graphics devices

Graphics devices can be specified precisely as a function in an R namespace.
For example, "grDevices:png". It is also possible to specify a generic graphical
device name that is a sequence of graphics devices to try. The first one in that
sequence that appears to be functioning is then selected.

For example, this is the case when
the graphics device option is set to "svg". The R package `svglite` is
the first to try in the sequence. If R fails to load that package there
are other  SVG devices to try try as alternatives.

To demonstrate this, let's set the graphics devices to "svg":

```python
import IPython
ipy = IPython.get_ipython()
ipy.magics_manager.registry['RMagics'].options.graphics_device_name = 'svg'
```

The output of the following magic depends on the R
packages installed on your system. If the R package `svglite` is installed
its device will be used. Otherwise alternatives will be tried.

```python
%Roptions show
```

### Options for graphics device

Graphics devices, selected from a generic names when the case (see above),
may havee options. These options can be specific to each graphics device.

**note: this is prefixed with an underscore to indicate that the API is
subject to changes.**

Options to display graphics are under `_options_display`. For example,
to change the default width:

```python
(
    ipy.magics_manager.registry['RMagics'].graphics_device
    ._options_display
    .width
) = 10
```

