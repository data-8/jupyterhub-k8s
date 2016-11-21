FROM debian:jessie

MAINTAINER Derrick Mar <derrickmar1215@berkeley.edu>

USER root

# Install all OS dependencies for notebook server that starts but lacks all
# features (e.g., download as all possible file formats)
ENV DEBIAN_FRONTEND noninteractive
RUN REPO=http://cdn-fastly.deb.debian.org \
 && echo "deb $REPO/debian jessie main\ndeb $REPO/debian-security jessie/updates main" > /etc/apt/sources.list \
 && apt-get update && apt-get -yq dist-upgrade \
 && apt-get install -yq --no-install-recommends \
    wget \
    bzip2 \
    ca-certificates \
    sudo \
    locales \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Housekeeping
RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen

# Configure Environment
ENV CONDA_DIR /opt/conda
ENV PATH $CONDA_DIR/bin:$PATH
ENV SHELL /bin/bash
ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8
ENV NB_USER jovyan
ENV NB_UID 1000

# INSTALL CONDA
RUN cd /tmp && \
    mkdir -p $CONDA_DIR && \
    wget --quiet https://repo.continuum.io/miniconda/Miniconda3-4.1.11-Linux-x86_64.sh && \
    echo "efd6a9362fc6b4085f599a881d20e57de628da8c1a898c08ec82874f3bad41bf *Miniconda3-4.1.11-Linux-x86_64.sh" | sha256sum -c - && \
    /bin/bash Miniconda3-4.1.11-Linux-x86_64.sh -f -b -p $CONDA_DIR && \
    rm Miniconda3-4.1.11-Linux-x86_64.sh && \
    $CONDA_DIR/bin/conda install --quiet --yes conda==4.1.11 && \
    $CONDA_DIR/bin/conda config --system --add channels conda-forge && \
    $CONDA_DIR/bin/conda config --system --set auto_update_conda false && \
    conda clean -tipsy

# INSTALL CONDA PACKAGES
RUN conda install --yes ipython==4.2.0
RUN conda install --yes jupyter_client==4.3.0
RUN conda install --yes notebook==4.2.1
RUN conda install --yes pip==8.1.2
RUN conda install --yes requests==2.10.0
RUN conda install --yes numpy==1.11.0

# INSTALL HUB
# Install JupyterHub to get the jupyterhub-singleuser startup script
# Use --pre to use 0.7 version
RUN pip install --no-cache-dir --pre jupyterhub

COPY apt_get_packages.txt /tmp/apt_get_packages.txt
RUN apt-get update && apt-get install -yq \
    $(grep -vE "^\s*#" /tmp/apt_get_packages.txt | tr "\n" " ") \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install git+https://github.com/data-8/nbinteract.git
RUN pip --no-cache-dir install pytest webargs requests gitpython toolz
RUN jupyter serverextension enable --system --py nbinteract
RUN jupyter nbextension install --system --py nbinteract
RUN jupyter nbextension enable --system --py nbinteract

# CLEANUP
RUN apt-get clean
RUN conda clean --all --yes

EXPOSE 8888

CMD jupyterhub-singleuser \
  --port=8888 \
  --ip=0.0.0.0 \
  --user="$JPY_USER" \
  --cookie-name=$JPY_COOKIE_NAME \
  --base-url=$JPY_BASE_URL \
  --hub-prefix=$JPY_HUB_PREFIX \
  --hub-api-url=$JPY_HUB_API_URL

