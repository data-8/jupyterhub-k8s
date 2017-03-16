#!/usr/bin/python3

""" Settings and constant values in backup scripts """

import os
import sys

class settings:

	def __init__(self):
		""" Set default values or retrieve them as environment variables """

		# The Google Cloud Project ID
		self.project_id = os.environ.get("PROJECT_ID", "92948014362")
		# The zone the project is hosted in 
		self.project_zone = os.environ.get("ZONE", "us-central1-a")
		# Namespace to filter disks on
		self.backup_namespace = os.environ.get("NAMESPACE", "kubernetes.io/created-for/pvc/namespace")
		# Shared disk name to filter disks on
		self.name_to_filter = os.environ.get("NAME_FILTER", "gke-prod-49ca6b0d-dyna-pvc")
		# The number of days to keep snapshots for
		self.retention_period = float(os.environ.get("RETENTION_PERIOD", 2))