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


class Inventory(command.Lister):
    """Base class for Inventory API.

    This is a workaround, the corrct way seems to be calling self.app.client_manager.inventory,
    but the module isn't registered for some reason.
    """

    def _get_api(self):
        hw_client = self.app.client_manager
        endpoint = hw_client.get_endpoint_for_service_type(service_type=SERVICE_TYPE)
        hw_api = api.BaseAPI(
            session=hw_client.session, service_type=SERVICE_TYPE, endpoint=endpoint
        )
        return hw_api


class ListHardware(command.Lister):
    """List all hw items in Doni."""

    api_path = "/v1/hardware/"
    columns = (
        "name",
        "project_id",
        "hardware_type",
        "properties",
    )

    def take_action(self, parsed_args):
        """List all hw items in Doni."""
        hw_api = Inventory._get_api(self)
        data = hw_api.list(self.api_path)

        data_iterator = (
            utils.get_dict_properties(s, self.columns, formatters={})
            for s in data.get("hardware")
        )
        return (self.columns, data_iterator)


class ExportHardware(ListHardware):
    """List all hw items in Doni."""

    api_path = "/v1/hardware/export/"
    columns = (
        "name",
        "project_id",
        "hardware_type",
        "properties",
        "uuid",
    )


class GetHardware(command.ShowOne):
    """List all hw items in Doni."""

    api_path = "/v1/hardware/"
    columns = (
        "name",
        "project_id",
        "hardware_type",
        "properties",
        "uuid",
    )

    def get_parser(self, prog_name):
        """Add arguments to cli parser."""
        parser = super(GetHardware, self).get_parser(prog_name)
        parser.add_argument("--name", metavar="<name>", help=("name of hw item"))
        parser.add_argument("--uuid", metavar="<uuid>", help=("uuid of hw item"))
        return parser

    def take_action(self, parsed_args):
        """List all hw items in Doni."""
        hw_api = Inventory._get_api(self)

        data = hw_api.find(self.api_path, value=parsed_args.name, attr="name")

        return (
            self.columns,
            utils.get_dict_properties(data, self.columns, formatters={}),
        )


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
