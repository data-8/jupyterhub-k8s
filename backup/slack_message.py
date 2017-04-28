#!/usr/bin/python3

""" Send logs to slack channel """

import requests
import logging


class slack_handler(logging.Handler):

    def __init__(self, token, channel="C510S0Z2L", username="blueprint-cluster"):
        logging.Handler.__init__(self, level=logging.INFO)
        self.token = token
        self.channel = channel
        self.username = username

    def message(self, text):
        if self.token:
            return requests.get(
                "https://slack.com/api/chat.postMessage?token=%s&channel=%s&text=%s&username=%s&as_user=true" % (
                    self.token,
                    self.channel,
                    "Autobackup: " + text,
                    self.username
                ))

    def emit(self, record):
        self.message(record.getMessage())