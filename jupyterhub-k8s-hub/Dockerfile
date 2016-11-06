FROM jupyterhub/jupyterhub-onbuild:0.6.1

MAINTAINER Ryan Lovett <rylo@berkeley.edu>

# upgrade pip
RUN pip install --upgrade pip

# Install dockerspawner and oauthenticator
RUN pip install git+git://github.com/docker/docker-py.git@1.8.1

# We're replacing dockerspanwer with kubespawner
# RUN pip install git+git://github.com/jupyterhub/dockerspawner.git@0.4.0
RUN pip --no-cache-dir install git+https://github.com/yuvipanda/jupyterhub-kubernetes-spawner.git@v0.1

# is this line needed anymore??
RUN /opt/conda/bin/pip install oauthenticator==0.4.*

# Install the statsd module for DataDog
RUN pip install statsd

# Add variable to allow connecting to the docker swarm
# ENV DOCKER_HOST https://127.0.0.1:2376

# Create oauthenticator directory -- this is where we'll put the userlist later
# RUN mkdir /srv/oauthenticator
# ENV OAUTHENTICATOR_DIR /srv/oauthenticator
# RUN chmod 700 /srv/oauthenticator

# add the userlist, spawner, and authenticator
# ADD swarmspawner.py /srv/oauthenticator/swarmspawner.py
# ADD systemuserspawner.py /srv/oauthenticator/systemuserspawner.py
# ADD docker_oauth.py /srv/oauthenticator/docker_oauth.py

# For nginx-chp
RUN apt-get -q update
RUN apt-get install -y --no-install-recommends ca-certificates nginx-extras lua-cjson
RUN pip --no-cache-dir install git+https://github.com/yuvipanda/jupyterhub-nginx-chp.git@3840564

# set working directory to the jupyterhub directory
WORKDIR /srv/jupyterhub

CMD ["jupyterhub", "-f", "/srv/jupyterhub/jupyterhub_config.py", "--no-ssl"]
