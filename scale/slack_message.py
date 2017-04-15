#!/usr/bin/python3

""" Send logs to slack channel """

import requests


class slack_handler:

    def __init__(self, token, channel="C48QN9GHK", username="autoscaler"):
        self.token = token
        self.channel = channel
        self.username = username

    def emit(self, text):
        if self.token:
            return requests.get(
                "https://slack.com/api/chat.postMessage?token=%s&channel=%s&text=%s&username=%s&as_user=true" % (
                    self.token,
                    self.channel,
                    text,
                    self.username
                ))
