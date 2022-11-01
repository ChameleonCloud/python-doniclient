import argparse
import json
import logging
from argparse import ArgumentParser, Namespace

from keystoneauth1.exceptions import HttpError
from osc_lib.command.command import ShowOne

from doniclient.osc import common as doni_common
from doniclient.v1 import resource_fields as res_fields

LOG = logging.getLogger(__name__)  # Get the logger of this module

from collections import namedtuple

PropertyFlag = namedtuple("PropertyFlag", ["flag", "type", "default"])

DEVICE_PROPERTIES = {
    "machine_name": PropertyFlag("machine-name", str, None),
    "contact_email": PropertyFlag("contact-email", str, None),
    "channels": PropertyFlag("channels", json.loads, None),
    "application_credential_id": PropertyFlag(
        "application-credential-id", str, None
    ),
    "application_credential_secret": PropertyFlag(
        "application-credential-secret", str, None
    ),
    "local_egress": PropertyFlag("local-egress", str, None),
}


class DeviceParser(doni_common.BaseParser):
    def get_parser(self, prog_name)-> ArgumentParser:
        parser =  super().get_parser(prog_name)
        parser.add_argument(
            "--name",
            help=(
                "Name of the hardware object. Best practice is to use a "
                "universally unique identifier, such has serial number or chassis ID. "
                "This will aid in disambiguating systems."
            ),
        )

        for prop_name, flag in DEVICE_PROPERTIES.items():
            parser.add_argument(
                f"--{flag.flag}",
                type=flag.type,
                default=flag.default,
                metavar=f"<{flag.flag}>",
                dest=f"properties.{prop_name}",
                action=doni_common.ExpandDotNotation
            )
        return parser


class CreateDevice(DeviceParser, ShowOne):
    """Create a Device Hardware Object in Doni.

    "Devices" are hosts that run user workloads in containers.
    Depending on the specified hardware type, differnt parameters are applicable.
    """

    needs_uuid = False

    def get_parser(self, prog_name)-> ArgumentParser:
        parser =  super().get_parser(prog_name)
        return parser

    def take_action(self, parsed_args: Namespace):
        """Create new HW item."""
        # Call superclass action to parse input json
        super().take_action(parsed_args)

        hw_client = self.app.client_manager.inventory
        # hw_type = "device"
        # FIXME(jason): 'device.balena' is really the only device type we use.
        # But, it's a bit awkard to have the user type this?
        hw_type = "device.balena"

        body = {
            "name": parsed_args.name,
            "hardware_type": hw_type,
            "properties": parsed_args.properties,
        }

        if parsed_args.dry_run:
            LOG.warn(parsed_args)
            LOG.warn(body)
            return

        try:
            data = hw_client.create(body)
        except HttpError as ex:
            LOG.error(ex.response.text)
            raise ex
        else:
            return data


class UpdateDevice(DeviceParser, doni_common.HardwarePatchCommand, ShowOne):
    """Update properties of existing device in inventory."""

    needs_uuid = True

    def get_parser(self, prog_name)-> ArgumentParser:
        parser =  super().get_parser(prog_name)
        return parser

    def take_action(self, parsed_args: Namespace):
        return super().take_action(parsed_args)

    def get_patch(self, parsed_args):
        patch = super().get_patch(parsed_args)

        field_map = {
            "name": "name",
        }

        for key, val in field_map.items():
            arg = getattr(parsed_args, key, None)
            if arg:
                patch.append({"op": "add", "path": f"/{val}", "value": arg})

        try:
            for key, val in parsed_args.properties.items():
                patch.append({"op": "add", "path": f"/properties/{key}", "value": val})
        except AttributeError:
            pass

        return patch
