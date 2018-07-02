FROM ubuntu:17.10

MAINTAINER Laurent Gautier <lgautier@gmail.com>

ARG DEBIAN_FRONTEND=noninteractive
ARG CRAN_MIRROR=https://cran.revolutionanalytics.com/

RUN \
  apt-get update -qq && \
  apt-get install -y \
                     apt-utils \
                     apt-transport-https \
		     dirmngr \
                     gnupg \
		     libcurl4-openssl-dev \
		     libnlopt-dev \
                     lsb-release && \
  echo "deb ${CRAN_MIRROR}/bin/linux/ubuntu $(lsb_release -c -s)/" \
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
		     libxml2-dev \
		     python3 \
		     python3-pip \
		     python3.6-venv \
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
        RSQLite\n\
        tidyr" > rpacks.txt && \
  R -e 'install.packages(sub("(.+)\\\\n","\\1", scan("rpacks.txt", "character")), repos="'"${CRAN_MIRROR}"'")' && \
  rm rpacks.txt

RUN \
  python3 -m pip --no-cache-dir install pip --upgrade && \
  python3 -m pip --no-cache-dir install setuptools --upgrade && \
  python3 -m pip --no-cache-dir install wheel --upgrade && \
  python3 -m pip --no-cache-dir install jinja2 numpy pandas pytest sphinx tzlocal && \
  rm -rf /root/.cache
  
# Run dev version of rpy2
RUN \
  python3 -m pip --no-cache-dir install \
       https://bitbucket.org/rpy2/rpy2/get/default.tar.gz && \
  rm -rf /root/.cache

