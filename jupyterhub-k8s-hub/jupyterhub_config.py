# Configuration file for Jupyter Hub
c = get_config()

import os
import sys
sys.path.insert(0, '/srv/oauthenticator')

# Base configuration
c.JupyterHub.log_level = "INFO"
c.JupyterHub.db_url = 'sqlite:////srv/jupyterhub_db/jupyterhub.sqlite'
c.JupyterHub.admin_access = True
c.JupyterHub.confirm_no_ssl = True
c.JupyterHub.proxy_check_interval = 30
# Use the nginx based proxy, rather than the nodejs one
c.JupyterHub.proxy_cmd = '/opt/conda/bin/nchp'

# Configure the authenticator
c.JupyterHub.authenticator_class = 'docker_oauth.DockerOAuthenticator'
c.DockerOAuthenticator.oauth_callback_url = os.environ['OAUTH_CALLBACK_URL']
c.DockerOAuthenticator.create_system_users = True
c.Authenticator.admin_users = admin = set()
#c.Authenticator.whitelist = whitelist = set()
c.GoogleOAuthenticator.hosted_domain = 'berkeley.edu'
c.GoogleOAuthenticator.login_service = 'UC Berkeley'

# Configure the spawner
c.JupyterHub.spawner_class = 'systemuserspawner.SystemUserSpawner'
c.SystemUserSpawner.container_image = 'data8/systemuser:nodrive'
c.DockerSpawner.tls_cert = os.environ['DOCKER_TLS_CERT']
c.DockerSpawner.tls_key = os.environ['DOCKER_TLS_KEY']
c.DockerSpawner.remove_containers = True
#c.DockerSpawner.read_only_volumes = {'/home/shared':'/home/shared'}
c.DockerSpawner.volumes = {'/home/shared':'/home/shared'}
c.DockerSpawner.extra_host_config = {'mem_limit': '2g'}
c.DockerSpawner.container_ip = "0.0.0.0"
#c.Spawner.start_timeout = 300
#c.Spawner.http_timeout = 150

# The docker instances need access to the Hub, so the default loopback port
# doesn't work. We need to tell the hub to listen on 0.0.0.0 because it's in a
# container, and we'll expose the port properly when the container is run. Then,
# we explicitly tell the spawned containers to connect to the proper IP address.
c.JupyterHub.proxy_api_ip = '0.0.0.0'
c.JupyterHub.hub_ip = '0.0.0.0'
c.DockerSpawner.hub_ip_connect = os.environ['HUB_IP']

# Add users to the admin list, the whitelist, and also record their user ids

with open('/srv/oauthenticator/userlist') as f:
    for line in f:
        if line.isspace(): continue
        parts = line.split()
        #whitelist.add(name)
        if len(parts) > 1 and parts[1] == 'admin':
            admin.add(parts[0])
