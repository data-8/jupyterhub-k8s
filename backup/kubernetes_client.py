#/usr/bin/python3

"""Provides read and write access to Kubernetes API"""
import logging
import sys

from kubernetes import client, config

backup_logger = logging.getLogger("backup")
logging.getLogger("kubernetes")

class k8s_control:

	"""Provides read and write access to Kubernetes API,
	and environment settings, including goals for the
	cluster always use the node and pods status at the
	time it was initiated"""

	def __init__(self, context="dev"):
		""" Needs to be initialized with options as an
		instance of settings"""
		self.context = self.configure_new_context(context)
		self.v1 = client.CoreV1Api()


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
		backup_logger.info("Successfully loaded %s context" % new_context)
		return context_to_activate


	def get_filtered_disk_names(self, namespace):
		"""Takes filtered PVs and returns their associated GCE disk names"""
		backup_logger.debug("Getting all GCE persistent disk names in namespace %s" % namespace)
		filtered_disk_names = []
		for disk in self.__get_filtered_pvs(namespace):
			filtered_disk_names.append(disk.spec.gce_persistent_disk.pd_name)
		return filtered_disk_names


	def __get_filtered_pvs(self, namespace):
		"""Return a list of Kubernetes persistent volumes belonging to NAMESPACE"""
		pvs = self.v1.list_persistent_volume().items
		eligible_pv_names = self.__get_pv_names_in_namespace(namespace)
		backup_logger.debug("Filtering disks by persistent volume claims")

		filtered_pvs = list(filter(lambda pv: \
			pv.metadata.name in eligible_pv_names, pvs))
		return filtered_pvs


	def __get_pv_names_in_namespace(self, namespace):
		"""Return a list of persistent volume claims belonging to the NAMESPACE"""
		pv_names = []
		backup_logger.debug("Getting all PV names from in namespace %s" % namespace)
		pvcs_in_namespace = self.v1.list_namespaced_persistent_volume_claim(namespace=namespace).items

		for pvc in pvcs_in_namespace:
			pv_names.append(pvc.spec.volume_name)
		return pv_names
