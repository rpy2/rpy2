FROM rpy2/rpy2:latest

MAINTAINER Laurent Gautier <lgautier@gmail.com>

ARG DEBIAN_FRONTEND=noninteractive

USER root

RUN \
  apt-get update -qq && \
  apt-get install -y npm nodejs-legacy && \
  rm -rf /var/lib/apt/lists/*

USER ${NB_USER}

# note: installing ipywidgets requires a follow-up "jupyter nbextension enable" 
RUN \
  pip3 --no-cache-dir install jupyter notebook && \
  pip3 --no-cache-dir install bokeh && \
  pip3 --no-cache-dir install ipywidgets && \
  jupyter nbextension enable --py --sys-prefix widgetsnbextension && \
  pip3 --no-cache-dir install jupyterhub && \
  rm -rf /root/.cache

ENV SHELL /bin/bash
ENV NB_USER jupyteruser
ENV HOME /home/${NB_USER}
ENV NB_UID 1000

# Create user
RUN useradd -m -s /bin/bash -N -u $NB_UID $NB_USER

# Grant sudo rights to install packages
RUN echo ${NB_USER} 'ALL=(ALL) NOPASSWD: /usr/bin/apt-get' >> /etc/sudoers

# Add Tini
ARG TINI_VERSION=v0.15.0
RUN wget --quiet https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini && \
    mv tini /usr/local/bin/tini && \
    chmod +x /usr/local/bin/tini

USER $NB_USER

# Setup  home directory and notebook config
RUN mkdir /home/$NB_USER/work && \
    mkdir /home/$NB_USER/.jupyter && \
    mkdir /home/$NB_USER/.local && \
    echo "cacert=/etc/ssl/certs/ca-certificates.crt" > /home/$NB_USER/.curlrc && \
    echo "c.NotebookApp.ip = '0.0.0.0'" >> /home/$NB_USER/.jupyter/jupyter_notebook_config.py && \
    python3.5 -m venv /home/$NB_USER/py35_env && \
    echo "source /home/$NB_USER/py35_env/bin/activate" >> /home/$NB_USER/.bashrc && \
    echo "echo Python virtual environment activated. Write \"deactivate\" to exit it." >> /home/$NB_USER/.bash

USER root

WORKDIR ${HOME}

EXPOSE 8888

ENTRYPOINT ["/usr/local/bin/tini", "--"]
CMD ["start-notebook.sh"]

# Add Jupyter script(s) emerging as ad hoc interface
RUN \
  git clone --depth=1 https://github.com/jupyter/docker-stacks.git && \
  cd docker-stacks/base-notebook && \
  cp start.sh /usr/local/bin/ && \
  cp start-notebook.sh /usr/local/bin/ && \
  cp start-singleuser.sh /usr/local/bin/ && \
  mkdir -p /etc/jupyter/ && \
  cp jupyter_notebook_config.py /etc/jupyter/ && \
  chown -R "${NB_USER}":users /etc/jupyter/ && \
  cd ../../ && \
  rm -rf docker-stacks

USER $NB_USER