FROM rpy2/rpy2:devel

MAINTAINER Laurent Gautier <lgautier@gmail.com>

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

ENV SHELL /bin/bash
ENV NB_USER jupyteruser
ENV NB_UID 1000

# Create user
RUN useradd -m -s /bin/bash -N -u $NB_UID $NB_USER

# Grant sudo rights to install packages
RUN echo ${NB_USER} 'ALL=(ALL) NOPASSWD: /usr/bin/apt-get' >> /etc/sudoers

# Add Tini
ENV TINI_VERSION v0.13.2
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /usr/local/bin/tini
RUN chmod +x /usr/local/bin/tini

USER $NB_USER

# Setup  home directory and notebook config
RUN mkdir /home/$NB_USER/work && \
    mkdir /home/$NB_USER/.jupyter && \
    mkdir /home/$NB_USER/.local && \
    echo "cacert=/etc/ssl/certs/ca-certificates.crt" > /home/$NB_USER/.curlrc && \
    echo "c.NotebookApp.ip = '0.0.0.0'" >> /home/$NB_USER/.jupyter/jupyter_notebook_config.py && \
    python3 -m venv /home/$NB_USER/py35_env && \
    echo "source /home/$NB_USER/py35_env/bin/activate" >> /home/$NB_USER/.bashrc && \
    echo "echo Python virtual environment activated. Write \"deactivate\" to exit it." >> /home/$NB_USER/.bash

USER root

WORKDIR /home/$NB_USER/work

EXPOSE 8888

USER $NB_USER

ENTRYPOINT ["/usr/local/bin/tini", "--"]
CMD jupyter notebook --no-browser
