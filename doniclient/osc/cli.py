"""Implements Doni command line interface."""

import logging

from keystoneauth1.exceptions import BadRequest, Conflict
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

    optional_args = [
        "ipmi_username",
        "ipmi_password",
        "ipmi_terminal_port",
    ]

    def get_parser(self, prog_name):
        """Add arguments to cli parser."""
        parser = super(CreateHardware, self).get_parser(prog_name)
        parser.add_argument(
            "--name",
            metavar="<name>",
            help=("human readable name of hw item"),
            required=True,
        )
        parser.add_argument(
            "--hardware_type",
            metavar="<hardware_type>",
            default="baremetal",
            help=("hardware_type of item"),
            required=True,
        )

        parser.add_argument("--mgmt_addr", metavar="<mgmt_addr>", required=True)
        parser.add_argument("--ipmi_username", metavar="<ipmi_username>")
        parser.add_argument("--ipmi_password", metavar="<ipmi_password>")
        parser.add_argument(
            "--ipmi_terminal_port", metavar="<ipmi_terminal_port>", type=int
        )

        parser.add_argument(
            "--interface",
            required_keys=["name", "mac"],
            action=parseractions.MultiKeyValueAction,
            help=(
                "Specify once per interface, in the form:\n `--interface name=<name>,mac=<mac_address>`"
            ),
        )
        return parser

    def take_action(self, parsed_args):
        """List all hw items in Doni."""
        json_body = {
            "name": parsed_args.name,
            "hardware_type": parsed_args.hardware_type,
            "properties": {
                "management_address": parsed_args.mgmt_addr,
                "interfaces": [],
            },
        }

        for interface_dict in parsed_args.interface:
            name = interface_dict.get("name")
            mac_addr = interface_dict.get("mac")

            json_body["properties"]["interfaces"].append(
                {
                    "name": name,
                    "mac_address": mac_addr,
                }
            )

        for arg in self.optional_args:
            json_body["properties"][arg] = getattr(parsed_args, arg)

        hw_client = self.app.client_manager.inventory
        try:
            data = hw_client.create(json_body)
        except (BadRequest, Conflict) as ex:
            print(f"got error {ex.response}: {ex.response.text}")
        else:
            return data


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
