import os
import sys

# Configuration file for Jupyter Hub
c = get_config()

# sys.path.insert(0, '/srv/oauthenticator')

# Use the nginx based proxy, rather than the nodejs one
c.JupyterHub.proxy_cmd = '/opt/conda/bin/nchp'
# Proxy and hub is running on the same machine
c.JupyterHub.ip = '0.0.0.0'

# Base configuration
c.JupyterHub.log_level = "INFO"
c.JupyterHub.db_url = 'sqlite:////srv/jupyterhub/jupyterhub.sqlite'
c.JupyterHub.admin_access = True
c.JupyterHub.confirm_no_ssl = True
c.JupyterHub.proxy_check_interval = 30

# Configure the authenticator
c.JupyterHub.authenticator_class = 'oauthenticator.GoogleOAuthenticator'

c.GoogleOAuthenticator.client_id = "92948014362-c7jc8k20co1e4eqmg8095818htadijat.apps.googleusercontent.com"
c.GoogleOAuthenticator.client_secret = "BabUWSqHd4ZekBqiaur4S1cm"
c.GoogleOAuthenticator.oauth_callback_url = os.environ['OAUTH_CALLBACK_URL']

c.GoogleOAuthenticator.hosted_domain = 'berkeley.edu'
c.GoogleOAuthenticator.login_service = 'UC Berkeley'

# print os.environ['OAUTH_CALLBACK_URL']

# c.DockerOAuthenticator.oauth_callback_url = os.environ['OAUTH_CALLBACK_URL']
# c.DockerOAuthenticator.create_system_users = True

### KUBESPAWNER STUFF
# Configure the spawner
c.JupyterHub.spawner_class = 'kubespawner.KubeSpawner'

c.KubeSpawner.kube_namespace = os.environ.get('POD_NAMESPACE', 'default')
c.KubeSpawner.kube_api_endpoint = 'https://{host}:{port}'.format(
    host=os.environ['KUBERNETES_SERVICE_HOST'],
    port=os.environ['KUBERNETES_SERVICE_PORT']
)

# Don't try to cleanup servers on exit - since in general for k8s, we want
# the hub to be able to restart without losing user containers
# c.JupyterHub.cleanup_servers = False

# First pulls can be really slow, so let's give it a big timeout
c.KubeSpawner.kube_ca_path = False
c.KubeSpawner.start_timeout = 60 * 5

c.KubeSpawner.singleuser_image_spec = 'data8/systemuser'

# The spawned containers need to be able to talk to the hub, ok through the proxy!
c.KubeSpawner.hub_ip_connect = '{host}:{port}'.format(
    host=os.environ['HUB_PROXY_SERVICE_HOST'],
    port=os.environ['HUB_PROXY_SERVICE_PORT']
)
### END KUBESPAWNER STUFF

# TODO: Look into what these do
c.Authenticator.whitelist = whitelist = set()
c.Authenticator.admin_users = {'cull', 'derrickmar1215'}

###
# c.SystemUserSpawner.container_image = 'data8/systemuser:nodrive'
# c.DockerSpawner.tls_cert = os.environ['DOCKER_TLS_CERT']
# c.DockerSpawner.tls_key = os.environ['DOCKER_TLS_KEY']
# c.DockerSpawner.remove_containers = True
###

#c.DockerSpawner.read_only_volumes = {'/home/shared':'/home/shared'}

###
# c.DockerSpawner.volumes = {'/home/shared':'/home/shared'}
# c.DockerSpawner.extra_host_config = {'mem_limit': '2g'}
# c.DockerSpawner.container_ip = "0.0.0.0"
###

#c.Spawner.start_timeout = 300
#c.Spawner.http_timeout = 150

# The docker instances need access to the Hub, so the default loopback port
# doesn't work. We need to tell the hub to listen on 0.0.0.0 because it's in a
# container, and we'll expose the port properly when the container is run. Then,
# we explicitly tell the spawned containers to connect to the proper IP address.
# c.JupyterHub.proxy_api_ip = '0.0.0.0'
# c.JupyterHub.hub_ip = '0.0.0.0'

###
# c.DockerSpawner.hub_ip_connect = os.environ['HUB_IP']
###

# Add users to the admin list, the whitelist, and also record their user ids

# with open('/srv/oauthenticator/userlist') as f:
#     for line in f:
#         if line.isspace(): continue
#         parts = line.split()
#         #whitelist.add(name)
#         if len(parts) > 1 and parts[1] == 'admin':
#             admin.add(parts[0])

