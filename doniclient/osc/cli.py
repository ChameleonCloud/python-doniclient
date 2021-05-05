"""Implements Doni command line interface."""

import json
import logging
from argparse import ArgumentParser, ArgumentTypeError
from typing import DefaultDict, List

from dateutil import parser, tz
from keystoneauth1.exceptions import BadRequest, HttpError, NotFound
from osc_lib import utils
from osc_lib.cli import parseractions
from osc_lib.command import command

LOG = logging.getLogger(__name__)  # Get the logger of this module


class DoniClientError(BaseException):
    """Base Error Class for Doni Client."""


class OutputFormat:
    columns = (
        "name",
        "project_id",
        "hardware_type",
        "properties",
        "uuid",
    )


class ParseUUID(command.Command):
    """Base class for show, sync, delete, and update."""

    def get_parser(self, prog_name):
        """Get uuid to use as path."""
        parser = super().get_parser(prog_name)
        parser.add_argument(
            dest="uuid", metavar="<uuid>", help=("unique ID of hw item")
        )
        return parser


class ListHardware(command.Lister):
    """List all hardware in the Doni database."""

    columns = OutputFormat.columns

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "--all",
            help="List hardware from all owners. Requires admin rights.",
            action="store_true",
        )
        return parser

    def take_action(self, parsed_args):
        """List all hw items in Doni."""
        hw_client = self.app.client_manager.inventory
        try:
            if parsed_args.all:
                data = hw_client.list()
            else:
                data = hw_client.export()
        except HttpError as ex:
            LOG.error(ex.response.text)
            raise ex

        data_iterator = (
            utils.get_dict_properties(s, self.columns, formatters={}) for s in data
        )
        return (self.columns, data_iterator)


class GetHardware(ParseUUID, command.ShowOne):
    """List specific hardware item in Doni."""

    columns = OutputFormat.columns

    def take_action(self, parsed_args):
        """List all hw items in Doni."""
        hw_client = self.app.client_manager.inventory
        try:
            data = hw_client.get_by_uuid(parsed_args.uuid)
        except HttpError as ex:
            LOG.error(ex.response.text)
            raise ex

        return (
            self.columns,
            utils.get_dict_properties(data, self.columns, formatters={}),
        )


class DeleteHardware(ParseUUID):
    """Delete specific hardware item in Doni."""

    def take_action(self, parsed_args):
        hw_client = self.app.client_manager.inventory
        try:
            result = hw_client.delete(parsed_args.uuid)
        except HttpError as ex:
            LOG.error(ex.response.text)
            raise ex

        return result.text


class SyncHardware(ParseUUID):
    """Sync specific hardware item in Doni."""

    def take_action(self, parsed_args):
        hw_client = self.app.client_manager.inventory
        try:
            result = hw_client.sync(parsed_args.uuid)
        except HttpError as ex:
            LOG.error(ex.response.text)
            raise ex

        return result.text


class ParseCreateArgs(command.Command):
    def _format_iface(self, interface_args: List):
        interface_list = []
        for interface in interface_args or []:
            interface_list.append(
                {
                    "name": interface.get("name"),
                    "mac_address": interface.get("mac"),
                }
            )
        return interface_list

    def _valid_date(self, s):
        LOG.debug(f"Processing Date {s}")
        try:
            parsed_dt = parser.parse(s)
            dt_with_tz = parsed_dt.replace(tzinfo=parsed_dt.tzinfo or tz.gettz())
            LOG.debug(dt_with_tz)
            return dt_with_tz
        except ValueError:
            msg = "Not a valid date: '{0}'.".format(s)
            raise ArgumentTypeError(msg)

    def _format_window(self, window_args):
        result = {}
        result["start"] = self._valid_date(window_args[0])
        result["end"] = self._valid_date(window_args[1])
        return result

    def _format_window_id(self, window_args):
        result = {}
        result["index"] = int(window_args[0])
        result["start"] = self._valid_date(window_args[1])
        result["end"] = self._valid_date(window_args[2])
        return result

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument("--dry_run", action="store_true")
        subparsers = parser.add_subparsers()

        parser.add_argument(
            "--name",
            metavar="<name>",
            help=(
                "Name of the hardware object. Best practice is to use a "
                "universally unique identifier, such has serial number or chassis ID. "
                "This will aid in disambiguating systems."
            ),
            required=True,
        )
        parser.add_argument(
            "--hardware_type",
            metavar="<hardware_type>",
            help=("hardware_type of item"),
            default="baremetal",
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
            required=True,
        )
        parser.add_argument(
            "--properties",
            action=parseractions.KeyValueAction,
            help=("Specify any extra properties as --extra <key>=<value>`"),
        )
        parser.add_argument(
            "--availability",
            action="append",
            nargs=2,
            metavar=("start", "end"),
            help="specify ISO compatible date for start and end of availability window",
        )
        return parser


class CreateHardware(ParseCreateArgs):
    """Create a Hardware Object in Doni."""

    def take_action(self, parsed_args):

        """Create new HW item."""
        hw_client = self.app.client_manager.inventory

        body = {
            "name": parsed_args.name,
            "hardware_type": parsed_args.hardware_type,
            "properties": {},
        }
        body["properties"]["management_address"] = parsed_args.mgmt_addr

        for arg in ["ipmi_username", "ipmi_password", "ipmi_terminal_port"]:
            value = getattr(parsed_args, arg)
            if value:
                body["properties"][arg] = value
        body["properties"]["interfaces"] = self._format_iface(parsed_args.interface)

        # Add any extra arguments
        body["properties"].update(parsed_args.properties)

        if parsed_args.dry_run:
            LOG.warn(parsed_args)
            LOG.warn(body)
        else:
            try:
                data = hw_client.create(body)
            except HttpError as ex:
                LOG.error(ex.response.text)
                raise ex

            return data


class ParseUpdateArgs(ParseUUID):
    def _format_iface(self, interface_args: List):
        interface_list = []
        key_map = {
            "name": "name",
            "mac_address": "mac",
        }
        for interface in interface_args or []:
            iface = {doni: interface.get(cmdline) for doni, cmdline in key_map}
            interface_list.append(iface)

        return interface_list

    def _valid_date(self, s):
        LOG.debug(f"Processing Date {s}")
        try:
            parsed_dt = parser.parse(s)
            dt_with_tz = parsed_dt.replace(tzinfo=parsed_dt.tzinfo or tz.gettz())
            LOG.debug(dt_with_tz)
            return dt_with_tz
        except ValueError:
            msg = "Not a valid date: '{0}'.".format(s)
            raise ArgumentTypeError(msg)

    def _format_window(self, window_args):
        result = {}
        result["start"] = self._valid_date(window_args[0])
        result["end"] = self._valid_date(window_args[1])
        return result

    def _format_window_id(self, window_args):
        result = {}
        result["index"] = int(window_args[0])
        result["start"] = self._valid_date(window_args[1])
        result["end"] = self._valid_date(window_args[2])
        return result

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument("--dry_run", action="store_true")
        subparsers = parser.add_subparsers()

        parser.add_argument(
            "--name",
            metavar="<name>",
            help=(
                "Name of the hardware object. Best practice is to use a "
                "universally unique identifier, such has serial number or chassis ID. "
                "This will aid in disambiguating systems."
            ),
            required=True,
        )
        parser.add_argument(
            "--hardware_type",
            metavar="<hardware_type>",
            help=("hardware_type of item"),
            required=True,
        )
        parser.add_argument("--mgmt_addr", metavar="<mgmt_addr>", required=True)
        parser.add_argument("--ipmi_username", metavar="<ipmi_username>")
        parser.add_argument("--ipmi_password", metavar="<ipmi_password>")
        parser.add_argument(
            "--ipmi_terminal_port", metavar="<ipmi_terminal_port>", type=int
        )

        iface_parser = subparsers.add_parser("interface")
        iface_parser.set_defaults(func=self._format_iface)
        iface_parser.add_argument(
            "--add",
            required_keys=["name", "mac"],
            action=parseractions.MultiKeyValueAction,
            help=(
                "Specify once per interface, in the form:\n `--interface name=<name>,mac=<mac_address>`"
            ),
        )
        iface_parser.add_argument(
            "--update",
            required_keys=["name", "mac", "index"],
            action=parseractions.MultiKeyValueAction,
            help=(
                "Specify once per interface, in the form:\n `--interface name=<name>,mac=<mac_address>,index=<index>`"
            ),
        )
        iface_parser.add_argument(
            "--delete",
            metavar="index",
            help=("Specify interface to delete, by index`"),
        )

        aw_parser = subparsers.add_parser("availability")
        aw_parser.add_argument(
            "--add",
            action="append",
            nargs=2,
            metavar=("start", "end"),
            help="specify ISO compatible date for start and end of availability window",
        )
        aw_parser.add_argument(
            "--update",
            action="append",
            nargs=3,
            metavar=("id", "start", "end"),
            help=("Specify window to update by ID, then start and end dates"),
        )
        aw_parser.add_argument(
            "--delete",
            metavar="id",
            type=int,
            action="append",
            help=("Specify window to delete by ID"),
        )
        return parser


class UpdateHardware(ParseUpdateArgs):
    """Send JSON Patch to update resource."""

    def get_parser(self, prog_name):
        """Add arguments to cli parser."""
        parser = super().get_parser(prog_name)
        self.parse_uuid(parser)
        self.parse_mgmt_args(parser, required=False)
        return parser

    def take_action(self, parsed_args):
        hw_client = self.app.client_manager.inventory
        uuid = parsed_args.uuid
        LOG.debug(parsed_args)
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

        # Update Interfaces
        for iface in self._format_iface(getattr(parsed_args, "iface_add")):
            patch.append({"op": "add", "path": f"/interface/-", "value": iface})

        for iface in self._format_iface(getattr(parsed_args, "iface_update")):
            index = iface.pop("index")
            patch.append(
                {"op": "replace", "path": f"/interface/{index}", "value": iface}
            )
        for iface in getattr(parsed_args, "iface_delete") or []:
            index = iface.get("index")
            patch.append({"op": "remove", "path": f"/interface/{index}"})

        # Update Availability Windows
        for aw in getattr(parsed_args, "aw_add") or []:
            window = self._format_window(aw)
            patch.append({"op": "add", "path": f"/availability/-", "value": window})

        for aw in getattr(parsed_args, "aw_update") or []:
            LOG.debug(aw)
            window = self._format_window_id(aw)
            index = window.pop("index")
            patch.append(
                {"op": "replace", "path": f"/availability/{index}", "value": window}
            )
        for index in getattr(parsed_args, "aw_delete") or []:
            patch.append(
                {"op": "remove", "path": f"/availability/{index}", "value": aw}
            )

        if patch:
            try:
                LOG.debug(f"PATCH_BODY:{patch}")
                data = hw_client.update(uuid, patch)
            except HttpError as ex:
                LOG.error(ex.response.text)
                raise ex
            else:
                return data.text
        else:
            LOG.warn("No updates to send")
