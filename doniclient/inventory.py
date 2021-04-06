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


class InventoryList(command.Lister):
    """Base class for Inventory API."""

    def _get_api(self):
        hw_client = self.app.client_manager
        endpoint = hw_client.get_endpoint_for_service_type(service_type=SERVICE_TYPE)
        hw_api = api.BaseAPI(
            session=hw_client.session, service_type=SERVICE_TYPE, endpoint=endpoint
        )
        return hw_api


class ListHardware(InventoryList):
    """List all hw items in Doni."""

    def take_action(self, parsed_args):
        """List all hw items in Doni."""
        hw_api = self._get_api()
        data = hw_api.list("/v1/hardware/")
        columns = (
            "name",
            "project_id",
            "hardware_type",
            "properties",
        )

        data_iterator = (
            utils.get_dict_properties(s, columns, formatters={})
            for s in data.get("hardware")
        )
        return (columns, data_iterator)


class ExportHardware(InventoryList):
    """List all hw items in Doni."""

    def take_action(self, parsed_args):
        """List all hw items in Doni."""
        hw_api = self._get_api()
        data = hw_api.list("/v1/hardware/export/")
        print(data)
        columns = (
            "name",
            "uuid",
            "project_id",
            "hardware_type",
            "properties",
        )

        data_iterator = (
            utils.get_dict_properties(s, columns, formatters={})
            for s in data.get("hardware")
        )
        return (columns, data_iterator)


class GetHardware(command.ShowOne):
    """List all hw items in Doni."""

    def get_parser(self, prog_name):
        """Add arguments to cli parser."""
        parser = super(Get, self).get_parser(prog_name)
        parser.add_argument("--uuid", metavar="<hw_uuid>", help=("UUID of hw item"))
        return parser

    def take_action(self, parsed_args):
        """List all hw items in Doni."""
        hw_api = self._get_api()
        response = hw_api.find(f"/v1/hardware/{parsed_args.hw_uuid}")
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
