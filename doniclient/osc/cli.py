"""Implements Doni command line interface."""

import argparse
import json
import logging
from argparse import FileType, Namespace
from collections import namedtuple

from keystoneauth1.exceptions import Conflict, HttpError
from osc_lib import utils as oscutils
from osc_lib.command import command

from doniclient.osc.common import (
    BaseParser,
    ExpandDotNotation,
    ExpandDotNotationAndStoreTrue,
    HardwarePatchCommand,
    conditional_action,
)
from doniclient.v1 import resource_fields as res_fields

LOG = logging.getLogger(__name__)  # Get the logger of this module

PropertyFlag = namedtuple("PropertyFlag", ["flag", "type", "default"])


class ListHardware(BaseParser, command.Lister):
    """List all hardware in the Doni database."""

    log = logging.getLogger(__name__ + ".ListHardware")

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "--all",
            help="List hardware from all owners. Requires admin rights.",
            action="store_true",
        )
        parser.add_argument(
            "--long",
            help="Include all columns.",
            action="store_true",
        )
        parser.add_argument(
            "--worker-type",
            metavar="<worker_type>",
            help="Filter by worker type",
            required=False,
            default="",
        )
        parser.add_argument(
            "--worker-state",
            help="Filter by worker state",
            choices=["PENDING", "IN_PROGRESS", "ERROR", "STEADY"],
            required=False,
            default="",
        )
        return parser

    def extract_workers_state(self, workers):
        # Extract worker types and their corresponding states and last errors from workers list
        worker_details = {}
        for worker in workers:
            worker_type = worker.get("worker_type")
            state = worker.get("state")
            last_error = worker.get("state_details", {}).get("last_error")
            if worker_type and (state or last_error):
                if worker_type not in worker_details:
                    worker_details[worker_type] = {}
                if state:
                    worker_details[worker_type]["state"] = state
                if last_error:
                    worker_details[worker_type]["last_error"] = last_error
        return worker_details

    def take_action(self, parsed_args):
        """List all hardware items in Doni."""

        hw_client = self.app.client_manager.inventory
        columns = res_fields.HARDWARE_RESOURCE.fields
        labels = list(res_fields.HARDWARE_RESOURCE.labels)  # Convert tuple to list

        if parsed_args.long:
            columns = res_fields.HARDWARE_DETAILED_RESOURCE.fields
            labels = list(
                res_fields.HARDWARE_DETAILED_RESOURCE.labels
            )  # Convert tuple to list

        # Fetch hardware data based on --all option
        if parsed_args.all:
            data = hw_client.export()
        else:
            data = hw_client.list()

        worker_types = []
        output_data = []

        # Extract filter values for better readability
        worker_type_filter = parsed_args.worker_type
        worker_state_filter = parsed_args.worker_state

        for hardware in data:
            workers = hardware.get("workers", [])
            worker_details = self.extract_workers_state(workers)

            # Apply worker type and state filters
            if (worker_type_filter and worker_type_filter not in worker_details) or (
                worker_state_filter
                and all(worker_state_filter != details["state"] for details in worker_details.values())
            ):
                continue

            output_item = oscutils.get_dict_properties(hardware, columns)

            # Apply combined worker type and state filter
            if worker_type_filter and worker_state_filter:
                details = worker_details.get(worker_type_filter, {})
                if worker_state_filter not in details["state"]:
                    continue

            for worker_type, details in worker_details.items():
                worker_state = details.get("state", "-")
                worker_error = details.get("last_error", "-")
                output_item = output_item + (worker_state,)
                output_item = output_item + (worker_error,)

                if worker_type not in worker_types:
                    worker_types.append(worker_type)
                    worker_types.append(worker_type + " last error")

            output_data.append(output_item)

        labels += worker_types  # Add worker types to labels list
        return labels, output_data



class GetHardware(BaseParser, command.ShowOne):
    """List specific hardware item in Doni."""

    needs_uuid = True

    def take_action(self, parsed_args):
        """List all hw items in Doni."""
        hw_client = self.app.client_manager.inventory
        try:
            data = oscutils.find_resource(hw_client, parsed_args.uuid)
        except HttpError as ex:
            LOG.error(ex.response.text)
            raise ex

        return self.dict2columns(data)


class DeleteHardware(BaseParser):
    """Delete specific hardware item in Doni."""

    needs_uuid = True

    def take_action(self, parsed_args):
        hw_client = self.app.client_manager.inventory
        try:
            data = oscutils.find_resource(hw_client, parsed_args.uuid)
        except HttpError as ex:
            LOG.error(ex.response.text)
            raise ex
        uuid = data["uuid"]
        try:
            hw_client.delete(uuid)
        except HttpError as ex:
            LOG.error(ex.response.text)
            raise ex


class SyncHardware(BaseParser):
    """Sync specific hardware item in Doni."""

    needs_uuid = True

    def take_action(self, parsed_args):
        hw_client = self.app.client_manager.inventory
        try:
            data = oscutils.find_resource(hw_client, parsed_args.uuid)
        except HttpError as ex:
            LOG.error(ex.response.text)
            raise ex
        uuid = data["uuid"]
        try:
            hw_client.sync(uuid)
        except HttpError as ex:
            LOG.error(ex.response.text)
            raise ex


def _add_prop_flag_group(parser, hardware_type, prop_flags, prog_name):
    """Register a mapping of flags for corresponding hardware properties.
    Args:
        parser (argparse.Parser): the parent parser
        group_name (str): the name of the new argument grouping. This is just used
            to visually group the properties in the CLI usage text.
        prop_flags (dict): a mapping of property names to PropertyFlag objects
            containing information about how the flag should be displayed and parsed.
            Importantly, the property name MUST match some field on the ``properties``
            dict on the target hardware type.
        prog_name (str): command executed (openstack hardware <set/unset>)
    """
    # Only store this flag in the resulting args if the hardware_type is in effect.
    condition_fn = lambda args: args.hardware_type == hardware_type
    group = parser.add_argument_group(f"{hardware_type} properties")
    for prop_name, flag in prop_flags.items():
        argument_params = {}
        argument_params["type"] = flag.type
        argument_params["default"] = flag.default
        argument_params["metavar"] = f"<{flag.flag}>"
        argument_params["dest"] = f"properties.{prop_name}"
        argument_params["action"] = conditional_action(ExpandDotNotation, condition_fn)
        if 'unset' in prog_name:
            argument_params["nargs"] = 0
            argument_params["type"] = None
            argument_params["default"] = None
            argument_params["metavar"] = None
            argument_params["action"] = conditional_action(ExpandDotNotationAndStoreTrue, condition_fn)
        group.add_argument(
            f"--{flag.flag}",
            **argument_params
        )


class HardwarePropertyFlags:
    baremetal_property_flags = {
        "management_address": PropertyFlag("management_address", str, None),
        "ipmi_username": PropertyFlag("ipmi_username", str, None),
        "ipmi_password": PropertyFlag("ipmi_password", str, None),
        "ipmi_terminal_port": PropertyFlag("ipmi_terminal_port", int, None),
        "baremetal_deploy_kernel_image": PropertyFlag(
            "deploy_kernel", str, None
        ),
        "baremetal_deploy_ramdisk_image": PropertyFlag(
            "deploy_ramdisk", str, None
        ),
        # FIXME(jason): why is the flag named ironic_?
        "baremetal_driver": PropertyFlag("ironic_driver", str, None),
        "baremetal_resource_class": PropertyFlag(
            "resource_class", str, "baremetal"
        ),
        "baremetal_capabilities": PropertyFlag(
            "capabilities", json.loads, None
        ),
        "cpu_arch": PropertyFlag("cpu_arch", str, "x86_64"),
        "node_type": PropertyFlag("blazar_node_type", str, None),
        "su_factor": PropertyFlag("blazar_su_factor", float, 1.0),
        "placement": PropertyFlag("placement", json.loads, None),
        "interfaces": PropertyFlag("interfaces", json.loads, {}),
    }
    device_property_flags = {
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


class CreateOrUpdateParser(BaseParser):
    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "--name",
            help=(
                "Name of the hardware object. Best practice is to use a "
                "universally unique identifier, such has serial number or chassis ID. "
                "This will aid in disambiguating systems."
            ),
        )
        parser.add_argument(
            "--hardware_type",
            default="baremetal",
            help=(
                "Type of hardware object. Each type of hardware takes different "
                "properties."
            ),
        )

        _add_prop_flag_group(
            parser,
            "baremetal",
            HardwarePropertyFlags.baremetal_property_flags,
            prog_name
        )

        _add_prop_flag_group(
            parser,
            "device",
            HardwarePropertyFlags.device_property_flags,
            prog_name
        )

        return parser


class CreateHardware(CreateOrUpdateParser):
    """Create a Hardware Object in Doni."""

    needs_uuid = False

    def get_parser(self, prog_name):
        return super().get_parser(prog_name)

    def take_action(self, parsed_args: Namespace):
        """Create new HW item."""
        # Call superclass action to parse input json
        super().take_action(parsed_args)

        hw_client = self.app.client_manager.inventory

        hw_type = parsed_args.hardware_type
        # FIXME(jason): 'device.balena' is really the only device type we use.
        # But, it's a bit awkard to have the user type this?
        if hw_type == "device":
            hw_type = "device.balena"

        body = {
            "name": parsed_args.name,
            "hardware_type": parsed_args.hardware_type,
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


class UpdateHardware(CreateOrUpdateParser, HardwarePatchCommand):
    """Update properties of existing hardware item."""

    needs_uuid = True

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)

        args_to_default = ("name", "properties")
        # Unset all defaults to avoid accidental changes
        for arg in parser._get_optional_actions():
            if arg.dest in args_to_default:
                arg.default = argparse.SUPPRESS

        return parser

    def get_patch(self, parsed_args):
        patch = []

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

    def take_action(self, parsed_args):
        hw_client = self.app.client_manager.inventory
        try:
            data = oscutils.find_resource(hw_client, parsed_args.uuid)
        except HttpError as ex:
            LOG.error(ex.response.text)
            raise ex
        uuid = data["uuid"]
        patch = self.get_patch(parsed_args)
        try:
            hw_client.update(uuid, patch)
        except HttpError as ex:
            LOG.error(ex.response.text)
            raise ex


class ImportHardware(BaseParser):
    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "--skip_existing",
            help="continue if an item already exists, rather than exiting",
            action="store_true",
        )
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
                    except Conflict as ex:
                        LOG.error(ex.response.text)
                        if parsed_args.skip_existing:
                            continue
                        else:
                            raise ex
                    else:
                        LOG.debug(data)


class UnsetHardware(UpdateHardware):
    """Unset properties of existing hardware item."""

    needs_uuid = True

    def get_patch(self, parsed_args):
        patch = []

        field_map = {
            "name": "name",
        }

        for key, val in field_map.items():
            arg = getattr(parsed_args, key, None)
            if arg:
                patch.append({"op": "remove", "path": f"/{val}", "value": arg})

        try:
            for key, val in parsed_args.properties.items():
                patch.append({"op": "remove", "path": f"/properties/{key}", "value": val})
        except AttributeError:
            pass

        return patch
