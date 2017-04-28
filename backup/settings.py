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
		# The slack token of the associated Slack Bot
		self.slack_token = os.environ.get("SLACK_TOKEN", "")
