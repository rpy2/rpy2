FROM ubuntu:16.04

MAINTAINER Laurent Gautier <lgautier@gmail.com>

RUN \
  apt-get update -qq && \
  apt-get install -y \
                     lsb-release && \
  echo "deb http://archive.ubuntu.com/ubuntu $(lsb_release -sc) multiverse\n" \
      >> /etc/apt/sources.list.d/added_repos.list && \
  echo "deb http://cran.cnr.berkeley.edu/bin/linux/ubuntu $(lsb_release -sc)/" \
      >> /etc/apt/sources.list.d/added_repos.list && \
  apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E084DAB9 && \
  apt-get update -qq && \
  apt-get install -y \
                     aptdaemon \
                     ed \
                     git \
		     mercurial \
		     libcairo-dev \
		     libedit-dev \
		     python3 \
		     python3-pip \
		     python3.5-venv \
		     r-base \
		     r-base-dev \
		     sudo \
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

# note: installing ipywidgets requires a follow-up "jupyter nbextension enable" 
RUN \
  pip3 --no-cache-dir install pip --upgrade && \
  pip3 --no-cache-dir install setuptools --upgrade && \
  pip3 --no-cache-dir install wheel --upgrade && \
  pip3 --no-cache-dir install numpy pandas sphinx jinja2 jupyter notebook && \
  pip3 --no-cache-dir install bokeh && \
  pip3 --no-cache-dir install ipywidgets && \
  jupyter nbextension enable --py --sys-prefix widgetsnbextension && \
  rm -rf /root/.cache

# Run dev version of rpy2
RUN \
  pip3 --no-cache-dir install \
       https://bitbucket.org/rpy2/rpy2/get/default.tar.gz && \
  rm -rf /root/.cache

ENV SHELL /bin/bash
ENV NB_USER jupyteruser
ENV NB_UID 1000

# Create user
RUN useradd -m -s /bin/bash -N -u $NB_UID $NB_USER

# Grant sudo rights to install packages
RUN echo ${NB_USER} 'ALL=(ALL) NOPASSWD: /usr/bin/apt-get' >> /etc/sudoers

# Add Tini
ENV TINI_VERSION v0.13.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /usr/local/bin/tini
RUN chmod +x /usr/local/bin/tini

USER $NB_USER

# Setup  home directory and notebook config
RUN mkdir /home/$NB_USER/work && \
    mkdir /home/$NB_USER/.jupyter && \
    mkdir /home/$NB_USER/.local && \
    echo "cacert=/etc/ssl/certs/ca-certificates.crt" > /home/$NB_USER/.curlrc && \
    echo "c.NotebookApp.ip = '*'" >> /home/$NB_USER/.jupyter/jupyter_notebook_config.py && \
    python3 -m venv /home/$NB_USER/py35_env && \
    echo "source /home/$NB_USER/py35_env/bin/activate" >> /home/$NB_USER/.bashrc && \
    echo "echo Python virtual environment activated. Write \"deactivate\" to exit it." >> /home/$NB_USER/.bash

USER root

WORKDIR /home/$NB_USER/work

EXPOSE 8888

USER $NB_USER

ENTRYPOINT ["/usr/local/bin/tini", "--"]
CMD jupyter notebook --no-browser
