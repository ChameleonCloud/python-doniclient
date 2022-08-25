import logging
from collections import namedtuple

from osc_lib.api import api

from doniclient.common import base

LOG = logging.getLogger(__name__)  # Get the logger of this module

class Hardware(base.Resource):
    def __repr__(self):
        return "<Hardware %s>" % self._info


class HardwareClient(api.BaseAPI):
    def __init__(self, session=None, service_type=None, endpoint=None, **kwargs):
        super().__init__(session, service_type, endpoint, **kwargs)

    def list(self, session=None, body=None, detailed=False, headers=None, **params):
        path = "/v1/hardware"
        ret =  super().list(path, session, body, detailed, headers, **params)
        hw_list = ret.get("hardware")
        obj_list = [Hardware(manager=base.Manager,info=h) for h in hw_list]
        return obj_list


