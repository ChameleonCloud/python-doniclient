"""Implements Doni command line interface."""

import logging

from osc_lib import utils
from osc_lib.cli import parseractions
from osc_lib.command import command

LOG = logging.getLogger(__name__)  # Get the logger of this module


class ListHardware(command.Lister):
    """List all hardware in the Doni database."""

    columns = (
        "name",
        "uuid",
        "project_id",
        "hardware_type",
        "properties",
    )

    def get_parser(self, prog_name):
        """Add arguments to cli parser."""
        parser = super(ListHardware, self).get_parser(prog_name)
        parser.add_argument("--name", metavar="<name>", help=("name of hw item"))
        parser.add_argument("--uuid", metavar="<uuid>", help=("uuid of hw item"))
        return parser

    def take_action(self, parsed_args):
        """List all hw items in Doni."""
        hw_client = self.app.client_manager.inventory
        data = hw_client.list()
        data_iterator = (
            utils.get_dict_properties(s, self.columns, formatters={}) for s in data
        )
        return (self.columns, data_iterator)


class ExportHardware(ListHardware):
    def take_action(self, parsed_args):
        """Export Public hw items in Doni."""
        hw_client = self.app.client_manager.inventory
        data = hw_client.export()

        data_iterator = (
            utils.get_dict_properties(s, self.columns, formatters={}) for s in data
        )
        return (self.columns, data_iterator)


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
        parser.add_argument("uuid", help=("uuid of hw item"))
        return parser

    def take_action(self, parsed_args):
        """List all hw items in Doni."""
        hw_client = self.app.client_manager.inventory
        try:
            data = hw_client.get_by_uuid(parsed_args.uuid)
        except Exception as ex:
            raise ex

        return (
            self.columns,
            utils.get_dict_properties(data, self.columns, formatters={}),
        )


class CreateHardware(command.Command):
    """Create a Hardware Object in Doni."""

    def get_parser(self, prog_name):
        """Add arguments to cli parser."""
        parser = super(GetHardware, self).get_parser(prog_name)
        parser.add_argument(
            "--name", metavar="<name>", help=("human readable name of hw item")
        )
        parser.add_argument(
            "--hardware_type",
            metavar="<hardware_type>",
            default="baremetal",
            help=("hardware_type of item"),
        )
        parser.add_argument(
            "--properties",
            metavar="<properties>",
            default={},
            help=("hardware_type of item"),
        )
        return parser

    def take_action(self, parsed_args):
        """List all hw items in Doni."""
        body = {
            "name": parsed_args.name,
            "hardware_type": parsed_args.hw_type,
            "properties": {},
        }

        hw_client = self.app.client_manager.inventory
        try:
            data = hw_client.create(body)
        except Exception as ex:
            raise ex

        return (
            self.columns,
            utils.get_dict_properties(data, self.columns, formatters={}),
        )


class UpdateHardware(command.Command):
    """Send JSON Patch to update resource."""

    def take_action(self, parsed_args):
        # Client manager interfaces are available to plugins.
        # This includes the OSC clients created.
        mgr = self.app.client_manager
        print("Foo")
        return


# class SyncResource(command.Command):
#     """Sync Resource."""

#     def take_action(self, parsed_args):
#         # Client manager interfaces are available to plugins.
#         # This includes the OSC clients created.
#         mgr = self.app.client_manager
#         print("Foo")
#         return
