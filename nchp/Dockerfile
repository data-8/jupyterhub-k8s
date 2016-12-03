FROM debian:jessie

RUN echo 'deb http://ftp.debian.org/debian jessie-backports main' >> /etc/apt/sources.list

RUN apt-get update

RUN apt-get install --yes --no-install-recommends -t jessie-backports\
    ca-certificates \
    nginx-extras \
    git \
    python3-pip \
    curl \
    lua-cjson

RUN apt-get install --yes wget

RUN pip3 install jinja2 traitlets
RUN pip3 install git+https://github.com/yuvipanda/jupyterhub-nginx-chp.git@master#egg=nchp

WORKDIR /usr/local/sbin
RUN wget https://dl.eff.org/certbot-auto
RUN chmod a+x ./certbot-auto

RUN apt-get install --yes --force-yes libssl-dev=1.0.1t-1+deb8u5 libssl1.0.0=1.0.1t-1+deb8u5

ARG DEBIAN_FRONTEND=noninteractive
RUN ./certbot-auto certonly -n --standalone -d example.com -d www.example.com

EXPOSE 8000

CMD /usr/local/bin/nchp --ip 0.0.0.0 --port 8000 --api-ip 0.0.0.0 --api-port 8001  --default-target http://${HUB_SERVICE_HOST}:${HUB_SERVICE_PORT}
