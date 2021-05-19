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

    require_hardware = False

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument("-d", "--dry-run", "--dry_run", action="store_true")
        if self.require_hardware:
            parser.add_argument(
                dest="uuid", metavar="<uuid>", help=("unique ID of hardware item")
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


class GetHardware(BaseParser, command.ShowOne):
    """List specific hardware item in Doni."""

    require_hardware = True
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


class DeleteHardware(BaseParser):
    """Delete specific hardware item in Doni."""

    require_hardware = True

    def take_action(self, parsed_args):
        hw_client = self.app.client_manager.inventory
        try:
            result = hw_client.delete(parsed_args.uuid)
        except HttpError as ex:
            LOG.error(ex.response.text)
            raise ex

        return result.text


class SyncHardware(BaseParser):
    """Sync specific hardware item in Doni."""

    require_hardware = True

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

        required_keys = ["mac_address"]
        optional_keys = ["name", "switch_info", "switch_port_id", "switch_id"]
        parser.add_argument(
            "--interface",
            required_keys=required_keys,
            optional_keys=optional_keys,
            action=parseractions.MultiKeyValueAction,
            help=(
                "Specify once per interface, in the form:"
                "`--interface key1=value1, key2=value2, ...`"
                f"\nRequired Keys are {required_keys}"
                f"\nOptional Keys are {optional_keys}"
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
        body["properties"]["interfaces"] = parsed_args.interface

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


class HardwarePatchCommand(BaseParser):
    require_hardware = True

    def get_patch(self, parsed_args):
        return []

    def take_action(self, parsed_args):
        hw_client = self.app.client_manager.inventory
        hw_uuid = parsed_args.uuid

        patch = self.get_patch(parsed_args)

        if parsed_args.dry_run:
            LOG.info(patch)
            return None

        if patch:
            try:
                LOG.debug(f"PATCH_BODY:{patch}")
                res = hw_client.update(hw_uuid, patch)
            except HttpError as ex:
                LOG.error(ex.response.text)
                raise ex
            else:
                return res.json()
        else:
            LOG.info("No updates to send")


class UpdateHardware(HardwarePatchCommand):
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
                "Specify once per interface, in the form:\n `--add name=<name>,mac=<mac_address>`"
            ),
        )
        parse_iface.add_argument(
            "--update",
            required_keys=["name", "mac", "index"],
            action=parseractions.MultiKeyValueAction,
            help=(
                "Specify once per interface, in the form:\n `--update name=<name>,mac=<mac_address>,index=<index>`"
            ),
        )
        parse_iface.add_argument(
            "--delete",
            metavar="index",
            help=("Specify interface to delete, by index`"),
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

    def get_patch(self, parsed_args):
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

        return patch


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
