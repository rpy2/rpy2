FROM rpy2/jupyter:latest

MAINTAINER Laurent Gautier <lgautier@gmail.com>

ARG CRAN_MIRROR=https://cran.revolutionanalytics.com/
ARG CRAN_MIRROR_TAG=-cran35

USER root

ARG LLVM_VERSION=7.0

RUN \
  add-apt-repository \
        --yes \
        'deb http://apt.llvm.org/'"$(lsb_release -c -s)"'/ llvm-toolchain-'"$(lsb_release -c -s)"'-7 main' && \
  wget -O - http://apt.llvm.org/llvm-snapshot.gpg.key|sudo apt-key add - && \
  apt-get update -qq && \
  apt-get install -y \
                     clang-"${LLVM_VERSION}" \
		     lldb-"${LLVM_VERSION}" \
                     ed \
                     git \
		     libcairo-dev \
		     libcurl4-openssl-dev \
		     libssl-dev \
		     libedit-dev \
		     scala \
		     wget && \
  rm -rf /var/lib/apt/lists/*

ARG SPARK_VERSION=2.4.3
RUN \
  wget --progress=bar http://mirrors.ocf.berkeley.edu/apache/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop2.7.tgz && \
  tar -xzf spark-${SPARK_VERSION}-bin-hadoop2.7.tgz && \
  mv spark-${SPARK_VERSION}-bin-hadoop2.7 /opt/ && \
  rm spark-${SPARK_VERSION}-bin-hadoop2.7.tgz

ARG LLVMLITE_VERSION=0.27.0
RUN \
  pip3 --no-cache-dir install wheel --upgrade && \
  pip3 --no-cache-dir install sqlalchemy && \
  rm -rf /root/.cache && \
  wget https://github.com/numba/llvmlite/archive/v${LLVMLITE_VERSION}.zip && \
  unzip v${LLVMLITE_VERSION}.zip && \
  cd llvmlite-${LLVMLITE_VERSION} && \
  LLVM_CONFIG=`which llvm-config-"${LLVM_VERSION}"` python3 setup.py install && \
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
