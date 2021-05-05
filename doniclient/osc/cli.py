"""Implements Doni command line interface."""

import json
import logging
from argparse import ArgumentTypeError, FileType
from sys import stdin
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


class BaseParser(command.Command):
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

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument("-d", "--dry-run", "--dry_run", action="store_true")
        return parser


class ParseUUID(BaseParser):
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


class CreateHardware(BaseParser):
    """Create a Hardware Object in Doni."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
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
        return parser

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


class UpdateHardware(ParseUUID):
    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)

        parser.add_argument(
            "--name",
            metavar="<name>",
            help=(
                "Name of the hardware object. Best practice is to use a "
                "universally unique identifier, such has serial number or chassis ID. "
                "This will aid in disambiguating systems."
            ),
        )
        parser.add_argument(
            "--hardware_type",
            metavar="<hardware_type>",
            help=("hardware_type of item"),
        )
        parser.add_argument("--mgmt_addr", metavar="<mgmt_addr>")
        parser.add_argument("--ipmi_username", metavar="<ipmi_username>")
        parser.add_argument("--ipmi_password", metavar="<ipmi_password>")
        parser.add_argument(
            "--ipmi_terminal_port", metavar="<ipmi_terminal_port>", type=int
        )

        subparsers = parser.add_subparsers(help="Select property to update.")

        parse_iface = subparsers.add_parser("interface")
        parse_iface.set_defaults(func=self._handle_ifaces)
        parse_iface.add_argument(
            "--add",
            required_keys=["name", "mac"],
            action=parseractions.MultiKeyValueAction,
            help=(
                "Specify once per interface, in the form:\n `--interface name=<name>,mac=<mac_address>`"
            ),
        )
        parse_iface.add_argument(
            "--update",
            required_keys=["name", "mac", "index"],
            action=parseractions.MultiKeyValueAction,
            help=(
                "Specify once per interface, in the form:\n `--interface name=<name>,mac=<mac_address>,index=<index>`"
            ),
        )
        parse_iface.add_argument(
            "--delete",
            metavar="index",
            help=("Specify interface to delete, by index`"),
        )

        aw_parser = subparsers.add_parser("availability")
        aw_parser.set_defaults(func=self._handle_windows)
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

    def _handle_ifaces(self, parsed_args):
        # Update Interfaces
        patch = []
        for iface in getattr(parsed_args, "add") or []:
            patch.append({"op": "add", "path": f"/interface/-", "value": iface})

        for iface in getattr(parsed_args, "update") or []:
            index = iface.pop("index")
            patch.append(
                {"op": "replace", "path": f"/interface/{index}", "value": iface}
            )
        for iface in getattr(parsed_args, "delete") or []:
            index = iface.get("index")
            patch.append({"op": "remove", "path": f"/interface/{index}"})
        return patch

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

    def _handle_windows(self, parsed_args):
        patch = []
        # Update Availability Windows
        for aw in getattr(parsed_args, "add") or []:
            window = self._format_window(aw)
            patch.append({"op": "add", "path": f"/availability/-", "value": window})

        for aw in getattr(parsed_args, "update") or []:
            LOG.debug(aw)
            window = self._format_window_id(aw)
            index = window.pop("index")
            patch.append(
                {"op": "replace", "path": f"/availability/{index}", "value": window}
            )
        for index in getattr(parsed_args, "delete") or []:
            patch.append({"op": "remove", "path": f"/availability/{index}"})
        return patch

    def take_action(self, parsed_args):
        """Send JSON Patch to update resource."""
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

        subparser = getattr(parsed_args, "func", None)
        if subparser:
            patch.extend(subparser(parsed_args))

        if parsed_args.dry_run:
            # LOG.warn(parsed_args)
            LOG.warn(patch)
            return None

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


class ImportHardware(BaseParser):
    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument("-f", "--file", help="JSON input file", type=FileType("r"))
        return parser

    def take_action(self, parsed_args):
        hw_client = self.app.client_manager.inventory
        with parsed_args.file as f:
            for item in json.load(f):
                if parsed_args.dry_run:
                    LOG.warn(item)
                else:
                    try:
                        data = hw_client.create(item)
                    except HttpError as ex:
                        LOG.error(ex.response.text)
                        raise ex
                    else:
                        LOG.debug(data)
