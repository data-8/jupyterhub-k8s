FROM debian:jessie

RUN apt-get update
RUN apt-get install -y --no-install-recommends python3 python3-pip ca-certificates git nginx-extras lua-cjson

# upgrade pip
RUN pip3 install --upgrade pip

RUN pip3 install --no-cache-dir --pre jupyterhub

RUN pip3 --no-cache-dir install git+https://github.com/jupyterhub/kubespawner.git
RUN pip3 --no-cache-dir install git+https://github.com/yuvipanda/jupyterhub-nginx-chp.git

ADD jupyterhub_config.py /srv/jupyterhub_config.py

# set working directory to the jupyterhub directory
WORKDIR /srv/jupyterhub

# JupyterHub API port
EXPOSE 8081

CMD ["jupyterhub", "-f", "/srv/jupyterhub_config.py", "--no-ssl"]
