"""Implements Doni API client."""
import json
import logging

# osc-lib interfaces available to plugins:
from osc_lib import clientmanager, exceptions, logs, utils
from osc_lib.api import api
from osc_lib.cli import parseractions
from osc_lib.command import command

LOG = logging.getLogger(__name__)  # Get the logger of this module

SERVICE_TYPE = "inventory"


class InventoryApi(command.Command):
    """Base class for Inventory API."""

    def _get_api(self):
        hw_client = self.app.client_manager
        endpoint = hw_client.get_endpoint_for_service_type(service_type=SERVICE_TYPE)
        hw_api = api.BaseAPI(
            session=hw_client.session, service_type=SERVICE_TYPE, endpoint=endpoint
        )
        return hw_api


class List(InventoryApi):
    """List all hw items in Doni."""

    def take_action(self, parsed_args):
        """List all hw items in Doni."""
        hw_api = self._get_api()
        response = hw_api.list("/v1/hardware/")
        return response


class Export(InventoryApi):
    """List all hw items in Doni."""

    def take_action(self, parsed_args):
        """List all hw items in Doni."""
        hw_api = self._get_api()
        response = hw_api.list("/v1/hardware/export/")
        return response


class Get(InventoryApi):
    """List all hw items in Doni."""

    def take_action(self, parsed_args):
        """List all hw items in Doni."""
        hw_api = self._get_api()
        response = hw_api.get("/v1/hardware/")
        return response


class Create(command.Command):
    """Create a Hardware Object in Doni."""

    def take_action(self, parsed_args):
        # InventoryAPI = api.BaseAPI(service_type=SERVICE_TYPE)
        # InventoryAPI.create()
        pass


class EnrollResource(command.Command):
    """Enroll Resource."""

    def take_action(self, parsed_args):
        # Client manager interfaces are available to plugins.
        # This includes the OSC clients created.
        mgr = self.app.client_manager
        print("Foo")
        return


class UpdateResource(command.Command):
    """Update Resource."""

    def take_action(self, parsed_args):
        # Client manager interfaces are available to plugins.
        # This includes the OSC clients created.
        mgr = self.app.client_manager
        print("Foo")
        return


class SyncResource(command.Command):
    """Sync Resource."""

    def take_action(self, parsed_args):
        # Client manager interfaces are available to plugins.
        # This includes the OSC clients created.
        mgr = self.app.client_manager
        print("Foo")
        return
