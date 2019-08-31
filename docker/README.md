This directory contains Dockerfile and associated scripts to build Docker images
for the rpy2 project.

## `base_rpy2/`

base `rpy2`.

```bash
docker build -t rpy2/rpy2 base_rpy2/
```


## `jupyter/`

`rpy2` with `jupyterlab` and selected extensions (e.g., `ipywidgets`)

```bash
docker build -t rpy2/jupyter jupyter_rpy2/
```

## `polyglot/`

`rpy2` with `jupyterlab`, `pyspark`, and various additional packages for my past
workshops on polyglot data analysis

``bash
docker build -t rpy2/polyglot polyglot_rpy2/
```
