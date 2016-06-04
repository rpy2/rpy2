FROM ubuntu:16.04

MAINTAINER Laurent Gautier <lgautier@gmail.com>

RUN \
  apt-get update -qq && \
  apt-get install -y \
                     ed \
                     git \
		     mercurial \
		     libcairo-dev \
		     libedit-dev \
                     lsb-release \
		     python3 \
		     python3-pip \
		     r-base \
		     r-base-dev \
		     wget &&\
  rm -rf /var/lib/apt/lists/*

RUN \
  echo "broom\n\
        dplyr\n\
        hexbin\n\
        ggplot2\n\
        lme4\n\
        tidyr" > rpacks.txt && \
  R -e 'install.packages(sub("(.+)\\\\n","\\1", scan("rpacks.txt", "character")), repos="http://cran.cnr.Berkeley.edu")' && \
  rm rpacks.txt

RUN \
  pip3 --no-cache-dir install pip --upgrade && \
  pip3 --no-cache-dir install setuptools --upgrade && \
  pip3 --no-cache-dir install wheel --upgrade && \
  pip3 --no-cache-dir install numpy pandas sphinx jinja2 jupyter notebook && \
  pip3 --no-cache-dir install bokeh && \
  rm -rf /root/.cache

# Run dev version of rpy2
RUN \
  pip3 --no-cache-dir install \
       https://bitbucket.org/rpy2/rpy2/get/version_2.8.x.tar.gz && \
  rm -rf /root/.cache

ENV SHELL /bin/bash
ENV NB_USER jupyteruser
ENV NB_UID 1000

# Create user
RUN useradd -m -s /bin/bash -N -u $NB_UID $NB_USER

USER $NB_USER

# Setup  home directory and notebook config
RUN mkdir /home/$NB_USER/work && \
    mkdir /home/$NB_USER/.jupyter && \
    mkdir /home/$NB_USER/.local && \
    echo "cacert=/etc/ssl/certs/ca-certificates.crt" > /home/$NB_USER/.curlrc && \
    echo "c.NotebookApp.ip = '*'" >> /home/$NB_USER/.jupyter/jupyter_notebook_config.py

USER root

WORKDIR /home/$NB_USER/work

EXPOSE 8888

USER $NB_USER

CMD jupyter notebook --no-browser
