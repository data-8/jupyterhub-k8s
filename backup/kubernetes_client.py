#/usr/bin/python3

"""Provides read and write access to Kubernetes API"""
import logging
import sys

from kubernetes import client, config

backup_logger = logging.getLogger("backup")
logging.getLogger("kubernetes").setLevel(logging.WARNING)

class k8s_control:

    """Provides read and write access to Kubernetes API,
    and environment settings, including goals for the
    cluster always use the node and pods status at the
    time it was initiated"""

    def __init__(self, options):
        """ Needs to be initialized with options as an
        instance of settings"""
        self.context = self.configure_new_context(options.default_context)
        self.options = options
        self.v1 = client.CoreV1Api()
        self.pods = self.get_pods()
        self.nodes = self.get_nodes()
        self.filtered_disks = self.get_filtered_disks()
        self.filtered_disk_names = self.get_filtered_disk_names()

    def configure_new_context(self, new_context):
        """ Loads .kube config to instantiate kubernetes
        with specified context"""
        contexts, _ = config.list_kube_config_contexts()
        try:
            contexts = [c['name'] for c in contexts]
            context_to_activate = list(
                filter(lambda context: new_context in context, contexts))
            assert len(context_to_activate) == 1  # avoid undefined behavior
            context_to_activate = context_to_activate[0]
        except (TypeError, IndexError):
            backup_logger.exception("Could not load context %s\n" % new_context)
            sys.exit(1)
        except AssertionError:
            backup_logger.fatal("Vague context specification")
            sys.exit(1)
        config.load_kube_config(context=context_to_activate)
        return context_to_activate

    def get_nodes(self):
        """Return a list of v1.Node"""
        backup_logger.debug("Getting all nodes in the cluster")
        return self.v1.list_node().items

    def get_pods(self):
        """Return a list of v1.Pod that needn't be omitted"""
        result = []
        backup_logger.debug("Getting all pods in all namespaces")
        pods = self.v1.list_pod_for_all_namespaces().items
        for pod in pods:
            result.append(pod)
        return result

    def get_filtered_disks(self):
        """Return a list of GCE Persistent Disks associated with notebook pods"""
        pvs = self.v1.list_persistent_volume().items
        pvcs = self.__get_pvcs_in_namespace()
        backup_logger.debug("Filtering disks by persistent volume claims")

        filtered_pvs = list(filter(lambda pv: \
            pv.spec.claim_ref.name in pvcs, pvs))
        return filtered_pvs

    def get_filtered_disk_names(self):
        """Takes filtered disks and returns their associated GCE PD names"""
        filtered_disk_names = []
        backup_logger.debug("Getting all GCE persistent disk names")
        for disk in self.filtered_disks:
            filtered_disk_names.append(disk.spec.gce_persistent_disk.pd_name)
        return filtered_disk_names

    def __get_pvcs_in_namespace(self):
        """Return a list of persistent volume claims belonging to POD_TYPE"""
        pvcs = []
        backup_logger.debug("Getting all persistent volume claims in relevant namespaces")
        for pod in self.pods:
            if pod.spec.volumes[0].persistent_volume_claim is not None \
                and pod.status.container_statuses[0].name in self.options.pvc_namespaces:
                pvcs.append(pod.spec.volumes[0].persistent_volume_claim.claim_name)
        return pvcs
