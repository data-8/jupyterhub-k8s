import os
import sys

# Configuration file for Jupyter Hub
c = get_config()

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

# Add an additional log file for debugging purposes
c.JupyterHub.extra_log_file = '/var/log/jupyterhub.log'
c.JupyterHub.log_level = 'DEBUG'

c.GoogleOAuthenticator.client_id = os.environ['GOOGLE_OAUTH_CLIENT_ID']
c.GoogleOAuthenticator.client_secret = os.environ['GOOGLE_OAUTH_CLIENT_SECRET']
c.GoogleOAuthenticator.oauth_callback_url = os.environ['OAUTH_CALLBACK_URL']

c.GoogleOAuthenticator.hosted_domain = 'berkeley.edu'
c.GoogleOAuthenticator.login_service = 'UC Berkeley'

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

c.KubeSpawner.singleuser_image_spec = 'data8/jupyterhub-k8s-user:data8_jupyterhubv2'

# The spawned containers need to be able to talk to the hub, ok through the proxy!
c.KubeSpawner.hub_ip_connect = '{host}:{port}'.format(
    host=os.environ['HUB_PROXY_SERVICE_HOST'],
    port=os.environ['HUB_PROXY_SERVICE_PORT']
)

# Allow culler to cull juptyerhub
c.JupyterHub.api_tokens = {
  os.environ['CULL_JHUB_TOKEN']: 'cull',
}
c.Authenticator.admin_users = {'cull', 'derrickmar1215'}

c.Authenticator.whitelist = whitelist = set()

