import dockerspawner

# urllib3 complains that we're making unverified HTTPS connections to swarm,
# but this is ok because we're connecting to swarm via 127.0.0.1. I don't
# actually want swarm listening on a public port, so I don't want to connect
# to swarm via the host's FQDN, which means we can't do fully verified HTTPS
# connections. To prevent the warning from appearing over and over and over
# again, I'm just disabling it for now.
import requests
requests.packages.urllib3.disable_warnings()

class SystemUserSpawner(dockerspawner.SystemUserSpawner):

    def _user_id_default(self):
        '''
           Without this, dockerspawner returns:
           KeyError: 'getpwnam(): name not found"
        '''
        self.log.info(self.user.state) # debug
        return self.user.state['user_id']
