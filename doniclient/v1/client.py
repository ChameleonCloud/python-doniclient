"""Creates doni client object."""
import json
import logging

import keystoneauth1.adapter

LOG = logging.getLogger(__name__)  # Get the logger of this module


class Client(object):
    def __init__(self, adapter: keystoneauth1.adapter, **kwargs):
        self.adapter = adapter

    def list(self):
        resp = self.adapter.get("/v1/hardware/")
        try:
            return resp.json().get("hardware")
        except json.JSONDecodeError:
            return resp

    def export(self):
        resp = self.adapter.get("/v1/hardware/export/")
        try:
            return resp.json().get("hardware")
        except json.JSONDecodeError:
            return resp

    def get_by_uuid(self, uuid):
        resp = self.adapter.get(f"/v1/hardware/{uuid}/")
        try:
            return resp.json()
        except json.JSONDecodeError:
            return resp
