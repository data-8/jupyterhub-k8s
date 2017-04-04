#!/usr/bin/python3

""" Shared settings and constant values across multiple scaling scripts"""

import os


class settings:

    env_delimiter = ':'

    def __init__(self):
        """Set default value"""
        self.max_utilization = float(os.environ.get("MAX_UTILIZATION", 0.85))
        self.min_utilization = float(os.environ.get("MIN_UTILIZATION", 0.65))
        self.optimal_utilization = float(
            os.environ.get("OPTIMAL_UTILIZATION", 0.75))
        self.min_nodes = int(os.environ.get("MIN_NODES", 3))
        self.max_nodes = int(os.environ.get("MAX_NODES", 35))

        # TODO: Get rid of these default values specific to Data8
        # Google Cloud configs
        self.zone = os.environ.get("ZONE", "us-central1-a")
        self.project = os.environ.get("PROJECT", "92948014362")

        # Azure configs
        self.location = ""
        self.subscription_id = ""
        self.client_id = ""
        self.secret = ""
        self.tenant_id = ""
        self.resource_group_name = ""
        self.container_service_name = ""

        self.preemptible_labels = os.environ.get(
            "PREEMPTIBLE_LABELS", "").split(self.env_delimiter)
        self.omit_labels = os.environ.get(
            "OMIT_LABELS", "").split(self.env_delimiter)
        self.omit_namespaces = os.environ.get(
            "OMIT_NAMESPACES", "kube-system").split(self.env_delimiter)

        self.test_cloud = True
        self.test_k8s = True
        self.yes = False

        self.context = ""
        self.context_cloud = ""

        # only used for debugging
        self.default_context = os.environ.get("DEFAULT_CONTEXT", "prod")
