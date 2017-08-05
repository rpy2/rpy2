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
        DBI\n\
        dbplyr\n\
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
  pip3 --no-cache-dir install numpy pandas sphinx jinja2 && \
  rm -rf /root/.cache
  
# Run dev version of rpy2
RUN \
  pip3 --no-cache-dir install \
       https://bitbucket.org/rpy2/rpy2/get/default.tar.gz && \
  rm -rf /root/.cache

