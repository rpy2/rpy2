FROM ubuntu:19.04

MAINTAINER Laurent Gautier <lgautier@gmail.com>

ARG DEBIAN_FRONTEND=noninteractive
ARG CRAN_MIRROR=https://cloud.r-project.org
ARG CRAN_MIRROR_TAG=-cran35

ARG RPY2_CFFI_MODE=BOTH

COPY install_apt.sh /opt/
COPY install_rpacks.sh /opt/
COPY install_pip.sh /opt/

RUN \
  sh /opt/install_apt.sh && \
  sh /opt/install_rpacks.sh && \
  sh /opt/install_pip.sh
  
# Run dev version of rpy2
RUN \
  python3 -m pip --no-cache-dir install https://github.com/rpy2/rpy2/archive/master.zip && \
  rm -rf /root/.cache

