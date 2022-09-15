"""Implements Doni command line interface."""


import argparse
import itertools
import json
import logging
from urllib import response

import keystoneauth1.exceptions as ksa_ex
from osc_lib import utils as oscutils
from osc_lib.command import command

LOG = logging.getLogger(__name__)  # Get the logger of this module

import doniclient.osc.common as common
from doniclient.v1 import resource_fields as res_fields


class ListHardware(command.Lister):
    """List all hardware in the Doni database."""

    log = logging.getLogger(__name__ + ".ListHardware")

    def get_parser(self, prog_name):
        parser = super(ListHardware, self).get_parser(prog_name)
        parser.add_argument(
            "--all",
            help="List hardware from all owners. Requires admin rights.",
            action="store_true",
        )
        display_group = parser.add_mutually_exclusive_group(required=False)
        display_group.add_argument(
            '--long',
            default=False,
            help=("Show detailed information about the nodes."),
            action='store_true')
        display_group.add_argument(
            '--fields',
            nargs='+',
            dest='fields',
            metavar='<field>',
            action='append',
            default=[],
            choices=res_fields.HARDWARE_DETAILED_RESOURCE.fields,
            help=("One or more node fields. Only these fields will be "
                   "fetched from the server. Can not be used when '--long' "
                   "is specified."))
        return parser


    def take_action(self, parsed_args):
        """List all hw items in Doni."""
        self.log.debug("take_action(%s)", parsed_args)
        client = self.app.client_manager.inventory

        columns = res_fields.HARDWARE_RESOURCE.fields
        labels = res_fields.HARDWARE_RESOURCE.labels

        params = {}
        if parsed_args.long:
            params['detail'] = parsed_args.long
            columns = res_fields.HARDWARE_DETAILED_RESOURCE.fields
            labels = res_fields.HARDWARE_DETAILED_RESOURCE.labels
        elif parsed_args.fields:
            params['detail'] = False
            fields = itertools.chain.from_iterable(parsed_args.fields)
            resource = res_fields.Resource(list(fields))
            columns = resource.fields
            labels = resource.labels
            params['fields'] = columns

        self.log.debug("params(%s)", params)
        if parsed_args.all:
            data = client.export()
        else:
            data = client.list()

        #set extra column for worker status
        for item in data:
            for worker,state,detail in common.get_worker_state_columns(item):
                state_column_name = f"worker_{worker}"
                detail_column_name = f"worker_{worker}_detail"
                setattr(item,state_column_name,state)
                setattr(item,detail_column_name,detail)

        result_list = (oscutils.get_item_properties(
                item=s,
                fields=columns,
                formatters={
                    'properties': common.JsonColumn,
                    'workers': common.JsonColumn,
                    }
            ) for s in data)

        return (labels,result_list)


class SyncHardware(command.Command):
    """Sync specific hardware item in Doni."""

    def get_parser(self, prog_name):
        parser =  super().get_parser(prog_name)
        parser.add_argument("uuid")
        return parser

    def take_action(self, parsed_args):
        hw_client = self.app.client_manager.inventory
        result = hw_client.sync(parsed_args.uuid)
        return result
        # try:
        # except ksa_ex.HttpError as ex:
        #     LOG.error(ex.response.text)
        #     raise ex
