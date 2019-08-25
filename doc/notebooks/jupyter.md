# Data Import

We choose to use an external dataset to demonstrate how R's own data import
features can be used.

```python
from rpy2.robjects.packages import importr
utils = importr('utils')

dataf = utils.read_csv('https://raw.githubusercontent.com/jakevdp/PythonDataScienceHandbook/'
                       'master/notebooks/data/california_cities.csv')
dataf
```

# Graphics

R has arguably some the best static visualizations, often looking more polished
than other visualization systems and this without the need to spend much
effort with them.

## Using `ggplot2`

```python
import rpy2.robjects.lib.ggplot2 as gp
```

Calling `ggplot2` looks pretty much like it would in R, which allows one to use the
all available documentation and examples available for the R package. Remember that
this is not a reimplementation of ggplot2 with inevitable differences and delay
for having the latest changes: the R package itself is generating the figures.

```python
p = (gp.ggplot(dataf) +
     gp.aes_string(x='longd',
                   y='latd',
                   color='population_total',
                   size='area_total_km2') +
     gp.geom_point() +
     gp.scale_color_continuous(trans='log10'))
```

```python
from rpy2.ipython.ggplot import image_png
image_png(p)
```

The figure can be customized to get closer to what we want.

```python
from rpy2.robjects.vectors import IntVector
p = (gp.ggplot(dataf) +
     gp.aes_string(x='longd',
                   y='latd',
                   color='population_total',
                   size='area_total_km2') +
     gp.geom_point(alpha=0.5) +
     # Axis definitions.
     gp.scale_x_continuous('Longitude') +
     gp.scale_y_continuous('Latitude') +
     # Custom size range.
     gp.scale_size(range = IntVector([1, 18])) +
     # Transform for pop -> color mapping
     gp.scale_color_continuous(trans='log10') +
     # Title.
     gp.ggtitle('California Cities: Area and Population') +
     # Plot theme and text size.
     gp.theme_light(base_size=16))
image_png(p)
```

## Using `ggplot2` extensions

To use the viridis color scale, we just need to import the corresponding R package, and write
3 lines of Python to extend `rpy2`'s ggplot2 wrapper with a new color scale.

```python
viridis = importr('viridis')
class ScaleColorViridis(gp.ScaleColour):
    _constructor = viridis.scale_color_viridis
scale_color_viridis = ScaleColorViridis.new
```

That new color scale can be used as any other scale already present in `ggplot2`:
```python
p = (gp.ggplot(dataf) +
     gp.aes_string(x='longd',
                   y='latd',
                   color='population_total',
                   size='area_total_km2') +
     gp.geom_point(alpha=0.5) +
     gp.scale_x_continuous('Longitude') +
     gp.scale_y_continuous('Latitude') +
     gp.scale_size(range = IntVector([1, 18])) +
     scale_color_viridis(trans='log10') +
     gp.ggtitle('California Cities: Area and Population') +
     gp.theme_light(base_size=16))
image_png(p)
```

So far we have shown that using `ggplot2` can be done from Python as if it
was just an other Python library for visualization, but R can also be used
in cells.

First the so-called "R magic" extension should be loaded.

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
%%R -w 800

cat("Running an R code cell.\n")

p <- ggplot(dataf) +
     aes_string(x = 'longd',
                y = 'latd',
                color = 'population_total',
                size = 'area_total_km2') +
     # TODO: alpha appears broken here.
     geom_point() +
     scale_x_continuous('Longitude') +
     scale_y_continuous('Latitude') +
     scale_size(range = c(1, 18)) +
     scale_color_viridis(trans='log10') +
     ggtitle('California Cities: Area and Population') +
     theme_light(base_size=16)
print(p)
```
