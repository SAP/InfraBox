# Utility class for slack integration

import os
import json
import requests

from pyinfraboxutils import get_env


class SlackHook(object):
    @property
    def hook_url(self):
        return self._hook_url

    def __init__(self, hook_url):
        self._hook_url = hook_url

    def send_status(self, message, mentions=None):
        if mentions:
            message = "{message} ({mentions})".format(message=message,
                                                      mentions=", ".join(self._wrap_mentions(mentions)))
        data = {
            "text": message
        }
        r = requests.post(self._hook_url, data=json.dumps(data))
        if r.status_code != 200:
            raise Exception("Posting to slack hook failed", r.text)

    @staticmethod
    def _wrap_mentions(mentions):
        if not isinstance(mentions, list):
            mentions = [mentions]
        # remove duplicates
        mentions = list(dict.fromkeys(mentions))
        # format names to <@name>
        return ["<@{}>".format(m) for m in mentions]
