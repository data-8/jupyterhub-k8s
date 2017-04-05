#!/usr/bin/python3

import logging
import sys

supported_platform = []

try:
    from googleapiclient import discovery
    from oauth2client.client import GoogleCredentials
    supported_platform.append("Google Cloud")
except ImportError:
    pass

try:
    from azure.common.credentials import ServicePrincipalCredentials
    from azure.mgmt.compute import ComputeManagementClient
    supported_platform.append("Microsoft Azure")
except ImportError:
    pass

scale_logger = logging.getLogger("scale")
scale_logger.info(
    "Can support cluster scaling on providers: %s", supported_platform)



class abstract_cluster_control:

    def __init__(self, options):
        """Needs to be initialized with options as an
        instance of settings"""
        pass

    def shutdown_specified_node(self, name):
        pass

    def add_new_node(self, cluster_size):
        """ONLY FOR CREATING NEW NODES to ensure
        new _node_number is running

        NOT FOR SCALING DOWN: random behavior expected
        TODO: Assert check that new_node_number is larger
        than current cluster size"""
        pass


class azure_cluster_control(abstract_cluster_control):

    """Abstracts cluster scaling logic for Microsoft Azure"""

    def __init__(self, options):
        """Needs to be initialized with options as an
        instance of settings"""

        self.options = options
        self.credentials = ServicePrincipalCredentials(
            client_id=options.client_id,
            secret=options.secret,
            tenant=options.tenant_id)
        self.compute = ComputeManagementClient(
            self.credentials, options.subscription_id)

        # TODO: determine based on context information?
        self.resource_group_name = options.resource_group_name
        self.container_service_name = options.container_service_name
        if options.context_cloud:
            self.agent_pool_name = self.__get_container_service_pool(
                self.__get_container_service(
                    self.resource_group_name, self.container_service_name),
                options.context_cloud
            ).name
        else:
            self.agent_pool_name = self.__get_container_service_pool(
                self.__get_container_service(
                    self.resource_group_name, self.container_service_name),
                options.context
            ).name

    def __get_container_service(self, resource_group_name, container_service_name):
        return self.compute.container_service.get(
            self.resource_group_name,
            self.container_service_name
        )

    def __get_container_service_pool(self, container_service, segment):
        pools = self.container_service.agent_pool_profiles
        matches = []
        for pool in pools:
            if segment in pool.name:
                matches.append(pool)
        if len(matches) == 0:
            scale_logger.exception(
                "Could not find context %s in Azure container services\n" % segment)
            sys.exit(1)
        elif len(matches) >= 2:
            scale_logger.fatal(
                "Vague context specification for Azure. Try to use --context-for-cloud to specify further")
            sys.exit(1)
        else:
            scale_logger.info(
                "Found managed pool %s for resizing", matches[0].name)
            return matches[0]

    def shutdown_specified_node(self, name):
        return self.compute.virtual_machine_scale_set_vms.deallocate(
            self.resource_group_name,
            self.agent_pool_name,
            self.__get_instance_id_from_name(name)
        )

    def __get_instance_id_from_name(self, name):
        # Azure python client is vague about it
        # Possible native RESTful solution
        # iterate through all vms
        # See
        # https://docs.microsoft.com/en-us/rest/api/virtualmachinescalesets/get-the-model-view-of-a-vm
        pass

    def add_new_node(self, cluster_size):
        """ONLY FOR CREATING NEW NODES to ensure
        new _node_number is running

        NOT FOR SCALING DOWN: random behavior expected
        TODO: Assert check that new_node_number is larger
        than current cluster size"""
        scale_logger.debug("Resizing cluster to: %d", cluster_size)
        container_service = self.__get_container_service(
            self.resource_group_name, self.container_service_name)
        agent_pool = self.__get_container_service_pool(
            container_service, self.agent_pool_name)
        assert cluster_size >= agent_pool.count
        agent_pool.count = cluster_size
        return self.compute.container_services.create_or_update(
            self.resource_group_name,
            self.container_service_name,
            container_service)


class gce_cluster_control(abstract_cluster_control):

    """Abstracts cluster scaling logic for Google Cloud"""

    def __init__(self, options):
        """Needs to be initialized with options as an
        instance of settings"""

        # Suppress weird warning during authentication
        logging.getLogger(
            'googleapiclient.discovery_cache').setLevel(logging.ERROR)

        self.options = options
        self.credentials = GoogleCredentials.get_application_default()
        self.compute = discovery.build(
            'compute', 'v1', credentials=self.credentials)
        self.zone = options.zone
        self.project = options.project
        self.group = self.__configure__managed_group_name(
            options.context_cloud)

    def __configure__managed_group_name(self, segment):
        "Use self.compute to find a managed group that matches the segment"
        managers = self.compute.instanceGroupManagers().list(
            zone=self.zone, project=self.project).execute()['items']
        matches = []
        for manager in managers:
            if segment in manager['name']:
                matches.append(manager)
        if len(matches) == 0:
            scale_logger.exception(
                "Could not find context %s in Google Cloud project\n" % segment)
            sys.exit(1)
        elif len(matches) >= 2:
            scale_logger.fatal(
                "Vague context specification for Google Cloud. Try to use --context-for-cloud to specify further")
            sys.exit(1)
        else:
            scale_logger.info(
                "Found managed pool %s for resizing", matches[0]['name'])
            return matches[0]

    def shutdown_specified_node(self, name):
        request_body = {
            "instances": [
                self.__get_node_url_from_name(name)
            ]
        }

        scale_logger.debug("Shutting down node: %s", name)

        return self.compute.instanceGroupManagers().deleteInstances(
            instanceGroupManager=self.group,
            project=self.project,
            zone=self.zone,
            body=request_body).execute()

    def add_new_node(self, cluster_size):
        """ONLY FOR CREATING NEW NODES to ensure
        new _node_number is running

        NOT FOR SCALING DOWN: random behavior expected
        TODO: Assert check that new_node_number is larger
        than current cluster size"""
        scale_logger.debug("Resizing cluster to: %d", cluster_size)

        return self.compute.instanceGroupManagers().resize(
            instanceGroupManager=self.group,
            project=self.project,
            zone=self.zone,
            size=cluster_size).execute()

    def list_managed_instances(self):
        """Lists the instances a part of the 
        specified cluster group"""
        scale_logger.debug("Gathering group: %s managed instances", self.group)
        result = self.compute.instanceGroupManagers().listManagedInstances(
            instanceGroupManager=self.group,
            project=self.project,
            zone=self.zone).execute()
        return result['managedInstances']

    def __get_node_url_from_name(self, name):
        """Gets the URL associated with the node name
        TODO: Error handling for invalid names"""
        node_url = ''
        instances = self.list_managed_instances()
        for instance in instances:
            instance_url = instance['instance']
            if name in instance_url:
                node_url = instance_url
                break
        scale_logger.debug("Node: %s has URL of: %s", name, node_url)
        return node_url
