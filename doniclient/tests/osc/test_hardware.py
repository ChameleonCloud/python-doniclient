import copy
import json
from unittest import mock
import uuid

from openstackclient.tests.unit import fakes, utils

from doniclient.osc import cli as hardware_cli
from doniclient.tests.osc import fakes as hardware_fakes


FAKE_HARDWARE_UUID = hardware_fakes.hardware_uuid

class TestHardware(hardware_fakes.TestHardware):
    def setUp(self):
        super(TestHardware, self).setUp()

        # Get a shortcut to the baremetal manager mock
        self.hardware_mock = self.app.client_manager.inventory
        self.hardware_mock.reset_mock()


class TestHardwareShow(TestHardware):
    def setUp(self):
        super().setUp()

        self.hardware_mock.get_by_uuid.return_value = (
            hardware_fakes.FakeHardware.create_one_hardware()
        )

        self.cmd = hardware_cli.GetHardware(self.app, None)

    def test_hardware_show(self):
        arglist = [FAKE_HARDWARE_UUID]
        verifylist = []

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        # DisplayCommandBase.take_action() returns two tuples
        columns, data = self.cmd.take_action(parsed_args)

        # Set expected values
        args = [FAKE_HARDWARE_UUID]

        self.hardware_mock.get_by_uuid.assert_called_with(*args)

        collist = (
            "created_at",
            "hardware_type",
            "name",
            "project_id",
            "properties",
            "updated_at",
            "uuid",
            "workers",
        )
        self.assertEqual(collist, columns)

        datalist = (
            hardware_fakes.hardware_created_at,
            hardware_fakes.hardware_baremetal_type,
            hardware_fakes.hardware_name,
            hardware_fakes.hardware_project_id,
            {},
            hardware_fakes.hardware_updated_at,
            hardware_fakes.hardware_uuid,
            [],
        )
        self.assertEqual(datalist, tuple(data))


class TestHardwareList(TestHardware):
    def setUp(self):
        super().setUp()

        self.hardware_mock.list.return_value = list(
            hardware_fakes.FakeHardware.create_one_hardware()
        )

        self.cmd = hardware_cli.ListHardware(self.app, None)

    def test_hardware_list(self):
        arglist = []
        verifylist = []

        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        # DisplayCommandBase.take_action() returns two tuples
        columns, data = self.cmd.take_action(parsed_args)

        # Set expected values
        args = []

        self.hardware_mock.list.assert_called_with(*args)


class TestHardwareCreate(TestHardware):
    def setUp(self):
        super().setUp()
        self.cmd = hardware_cli.CreateHardware(self.app, None)


class TestHardwareDelete(TestHardware):
    def setUp(self):
        super().setUp()
        self.cmd = hardware_cli.DeleteHardware(self.app, None)


class TestHardwareSet(TestHardware):
    def setUp(self):
        super().setUp()
        self.cmd = hardware_cli.UpdateHardware(self.app, None)

    def test_hardware_update(self):
        self.hardware_mock.update.return_value = hardware_fakes.FakeHardware.create_one_hardware()

        fake_mgmt_address = "fake-mgmt_addr"
        arglist = [FAKE_HARDWARE_UUID, "--mgmt_addr", fake_mgmt_address]
        parsed_args = self.check_parser(self.cmd, arglist, [])
        assert parsed_args.properties == {"mgmt_addr": fake_mgmt_address}

        self.cmd.take_action(parsed_args)
        self.hardware_mock.update.assert_called_with(FAKE_HARDWARE_UUID, [{
            "op": "add", "path": "/properties/mgmt_addr", "value": fake_mgmt_address
        }])

class TestHardwareSync(TestHardware):
    def setUp(self):
        super().setUp()
        self.cmd = hardware_cli.SyncHardware(self.app, None)
