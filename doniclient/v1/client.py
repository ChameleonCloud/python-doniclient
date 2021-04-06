"""Creates doni client object."""
import logging

from osc_lib.api import api

LOG = logging.getLogger(__name__)  # Get the logger of this module


class Client(api.BaseAPI):
    def __init__(self, session, service_type, endpoint, **kwargs):
        super().__init__(
            session=session, service_type=service_type, endpoint=endpoint, **kwargs
        )

    def list(self, **kwargs):
        return super().list(path="/v1/hardware/" ** kwargs)

    def export(self, **kwargs):
        return super().list(path="/v1/hardware/export/", **kwargs)
