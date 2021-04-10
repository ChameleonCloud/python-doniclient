"""Implements Doni command line interface."""

import logging
from typing import List

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
    """Export public fields from the hw db."""

    def take_action(self, parsed_args):
        """Export Public hw items in Doni."""
        hw_client = self.app.client_manager.inventory
        data = hw_client.export()

        data_iterator = (
            utils.get_dict_properties(s, self.columns, formatters={}) for s in data
        )
        return (self.columns, data_iterator)


class GetHardware(command.ShowOne):
    """List specific hardware item in Doni."""

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


class HardwareAction(command.Command):
    """Base class for create and update."""

    def __init__(self, app, app_args, cmd_name):
        super().__init__(app, app_args, cmd_name=cmd_name)

    optional_args = [
        "ipmi_username",
        "ipmi_password",
        "ipmi_terminal_port",
    ]

    columns = (
        "name",
        "project_id",
        "hardware_type",
        "properties",
        "uuid",
    )

    def _get_mgmt_args(self, parser, required: bool = True):
        parser.add_argument(
            "--name",
            metavar="<name>",
            help=("human readable name of hw item"),
            required=required,
        )
        parser.add_argument(
            "--hardware_type",
            metavar="<hardware_type>",
            help=("hardware_type of item"),
            required=required,
        )
        parser.add_argument("--mgmt_addr", metavar="<mgmt_addr>", required=required)
        parser.add_argument("--ipmi_username", metavar="<ipmi_username>")
        parser.add_argument("--ipmi_password", metavar="<ipmi_password>")
        parser.add_argument(
            "--ipmi_terminal_port", metavar="<ipmi_terminal_port>", type=int
        )

        return parser

    def get_parser(self, prog_name):
        """Add arguments to cli parser."""
        parser = super(HardwareAction, self).get_parser(prog_name)
        parser.add_argument("--dry_run", action="store_true")
        parser.add_argument(
            "--interface",
            required_keys=["name", "mac"],
            action=parseractions.MultiKeyValueAction,
            help=(
                "Specify once per interface, in the form:\n `--interface name=<name>,mac=<mac_address>`"
            ),
        )
        parser.add_argument(
            "--aw_add",
            required_keys=["start", "end"],
            action=parseractions.MultiKeyValueAction,
            help=(
                "Specify once per window to add:\n`--window start=<start>,end=<end>`"
            ),
        )
        parser.add_argument(
            "--aw_update",
            required_keys=["id", "start", "end"],
            action=parseractions.MultiKeyValueAction,
            help=(
                "Specify once per window to update:\n"
                "`--aw_update id=<id>,start=<start>,end=<end>`"
            ),
        )
        parser.add_argument(
            "--aw_delete",
            metavar="id",
            action="append",
            help=("Specify once per window to delete: `--aw_delete <id>`"),
        )
        parser.add_argument(
            "--extra",
            metavar="<key>=<value>",
            action=parseractions.KeyValueAction,
            help=("specify key=<value> to add to hw properties"),
        )
        return parser

    def _parse_interfaces(self, interface_args: List):
        interface_list = []
        for interface in interface_args or []:
            interface_list.append(
                {
                    "name": interface.get("name"),
                    "mac_address": interface.get("mac"),
                }
            )
        return interface_list


class CreateHardware(HardwareAction):
    """Create a Hardware Object in Doni."""

    def __init__(self, app, app_args, cmd_name):
        super().__init__(app, app_args, cmd_name=cmd_name)

    def get_parser(self, prog_name):
        base_parser = super().get_parser(prog_name)
        parser = self._get_mgmt_args(base_parser, required=True)
        return parser

    def take_action(self, parsed_args):
        """List all hw items in Doni."""
        hw_client = self.app.client_manager.inventory

        properties = {}
        properties["management_address"] = parsed_args.mgmt_addr
        properties["interfaces"] = self._parse_interfaces(parsed_args.interface)

        # Set optional arguments
        for arg in self.optional_args:
            properties[arg] = getattr(parsed_args, arg)

        body = {
            "name": parsed_args.name,
            "hardware_type": parsed_args.hardware_type,
            "properties": properties,
        }

        if parsed_args.dry_run:
            print(body)
        else:
            try:
                data = hw_client.create(body)
            except (BadRequest, Conflict) as ex:
                print(f"got error {ex.response}: {ex.response.text}")
                raise
            else:
                return data


class UpdateHardware(HardwareAction):
    """Send JSON Patch to update resource."""

    def __init__(self, app, app_args, cmd_name):
        super().__init__(app, app_args, cmd_name=cmd_name)

    def get_parser(self, prog_name):
        """Add arguments to cli parser."""
        base_parser = super().get_parser(prog_name)
        parser = self._get_mgmt_args(base_parser, False)
        parser.add_argument(
            dest="uuid",
            metavar="<uuid>",
            help=("unique ID of hw item"),
        )
        return parser

    def take_action(self, parsed_args):
        hw_client = self.app.client_manager.inventory

        uuid = parsed_args.uuid

        patch = []

        field_map = {
            "name": "name",
            "hardware_type": "hardware_type",
            "management_address": "properties/management_address",
            "ipmi_username": "properties/ipmi_username",
            "ipmi_password": "properties/ipmi_password",
            "ipmi_terminal_port": "properties/ipmi_terminal_port",
        }

        for key, val in field_map.items():
            arg = getattr(parsed_args, key, None)
            if arg:
                patch.append({"op": "add", "path": f"/{val}", "value": arg})

        interfaces = self._parse_interfaces(getattr(parsed_args, "interface"))
        for iface in interfaces:
            name = iface.get("name")
            patch.append({"op": "add", "path": f"/interface/{name}", "value": iface})

        for aw in getattr(parsed_args, "aw_add") or []:
            patch.append({"op": "add", "path": f"/availability/-", "value": aw})

        for aw in getattr(parsed_args, "aw_update") or []:
            patch.append(
                {"op": "replace", "path": f"/availability/{name}", "value": aw}
            )

        for aw in getattr(parsed_args, "aw_delete") or []:
            patch.append({"op": "remove", "path": f"/availability/{name}", "value": aw})

        try:
            LOG.debug(f"PATCH_BODY:{patch}")
            data = hw_client.update(uuid, patch)
        except (BadRequest, Conflict) as ex:
            print(f"got error: {ex.response.text}")
            raise
        else:
            return data.text
