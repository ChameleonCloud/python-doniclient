"""Creates doni client object."""
import json
import logging

from keystoneauth1.adapter import Adapter as ksa_adapter

LOG = logging.getLogger(__name__)  # Get the logger of this module


class Client(object):
    def __init__(self, adapter: ksa_adapter, **kwargs):
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

    def get(self, name_or_uuid):
        return self.get_by_uuid(name_or_uuid)

    def get_availability(self, hardware_uuid: str):
        resp = self.adapter.get(f"/v1/hardware/{hardware_uuid}/availability")
        try:
            return resp.json().get("availability", [])
        except json.JSONDecodeError:
            return resp

    def create(self, json, **kwargs):
        """Create a hw object in the doni DB."""
        resp = self.adapter.post("/v1/hardware/", json=json)
        try:
            return resp.json()
        except json.JSONDecodeError:
            return resp

    def delete(self, name_or_uuid):
        hardware_list = self.list()
        matching_hardware = [h for h in hardware_list if h['name'] == name_or_uuid]
        hardware_uuid = name_or_uuid
        if matching_hardware:
            hardware_uuid = matching_hardware[0]['uuid']
        return self.adapter.delete(f"/v1/hardware/{hardware_uuid}/")
        

    def sync(self, uuid):
        return self.adapter.post(f"/v1/hardware/{uuid}/sync")

    def update(self, name_or_uuid, json):
        hardware_list = self.list()
        matching_hardware = [h for h in hardware_list if h['name'] == name_or_uuid]
        hardware_uuid = name_or_uuid
        if matching_hardware:
            hardware_uuid = matching_hardware[0]['uuid']
        resp = self.adapter.patch(f"/v1/hardware/{hardware_uuid}/", json=json)
        try:
            return resp.json()
        except json.JSONDecodeError:
            return resp
