FROM rpy2/jupyter:latest

MAINTAINER Laurent Gautier <lgautier@gmail.com>

ARG CRAN_MIRROR=https://cran.revolutionanalytics.com/

USER root

RUN \
  echo 'deb http://apt.llvm.org/xenial/ llvm-toolchain-xenial-5.0 main' >> /etc/apt/sources.list && \
  wget -O - http://apt.llvm.org/llvm-snapshot.gpg.key|sudo apt-key add - && \
  apt-get update -qq && \
  apt-get install -y \
                     clang-5.0 \
		     lldb-5.0 \
                     ed \
                     git \
		     libcairo-dev \
		     libedit-dev \
		     scala \
		     wget && \
  rm -rf /var/lib/apt/lists/*

ARG SPARK_VERSION=2.2.1
RUN \
  wget --progress=bar http://mirrors.ocf.berkeley.edu/apache/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop2.7.tgz && \
  tar -xzf spark-${SPARK_VERSION}-bin-hadoop2.7.tgz && \
  mv spark-${SPARK_VERSION}-bin-hadoop2.7 /opt/ && \
  rm spark-${SPARK_VERSION}-bin-hadoop2.7.tgz

ARG LLVMLITE_VERSION=0.21.0
RUN \
  pip3 --no-cache-dir install wheel --upgrade && \
  pip3 --no-cache-dir install sqlalchemy && \
  rm -rf /root/.cache && \
  wget https://github.com/numba/llvmlite/archive/v${LLVMLITE_VERSION}.zip && \
  unzip v${LLVMLITE_VERSION}.zip && \
  cd llvmlite-${LLVMLITE_VERSION} && \
  LLVM_CONFIG=`which llvm-config-5.0` python3 setup.py install && \
  cd .. && rm -rf llvmlite-${LLVMLITE_VERSION} && rm v${LLVMLITE_VERSION}.zip && \
  pip3 --no-cache install numba && \
  pip3 --no-cache install findspark && \
  pip3 --no-cache install jupyter_dashboards && \
  jupyter dashboards quick-setup --sys-prefix && \
  rm -rf /root/.cache

RUN \
  echo "bigrquery\n\
        glmnet\n\
        gridExtra\n\
        maps\n\
        mapproj\n\
        plotly\n\
        RPostgreSQL\n\
        party\n\
        partykit\n\
        svglite" > rpacks.txt && \
  R -e 'install.packages(sub("(.+)\\\\n","\\1", scan("rpacks.txt", "character")), repos="'"${CRAN_MIRROR}"'")' && \
  rm rpacks.txt

ENV NB_USER jupyteruser
ENV SPARK_HOME /opt/spark-${SPARK_VERSION}-bin-hadoop2.7 

USER $NB_USER
RUN mkdir -p /home/$NB_USER/work

WORKDIR /home/$NB_USER/work
