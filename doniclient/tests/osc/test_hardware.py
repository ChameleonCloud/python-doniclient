from doniclient.osc import cli as hardware_cli
from doniclient.tests.osc import fakes as hardware_fakes
from osc_lib import utils as oscutils
from osc_lib import exceptions
import unittest
FAKE_HARDWARE_UUID = hardware_fakes.hardware_uuid
FAKE_HARDWARE_NAME = hardware_fakes.hardware_name

UPDATE_PARAMS = [
    (
        "baremetal",
        "--management_address",
        "management_address",
        "/properties/management_address",
        "fake-mgmt_addr",
        True,
    ),
    (
        "device",
        "--machine-name",
        "machine_name",
        "/properties/machine_name",
        "jetson-nano",
        False,
    ),
    (
        "device",
        "--contact-email",
        "contact_email",
        "/properties/contact_email",
        "test@foo.bar",
        True,
    ),
    ("device", "--local-egress", "local_egress", "/properties/local_egress", "allow", False),
]


class TestHardware(hardware_fakes.TestHardware):
    def setUp(self):
        super(TestHardware, self).setUp()

        # Get a shortcut to the baremetal manager mock
        self.hardware_mock = self.app.client_manager.inventory
        self.hardware_mock.reset_mock()


class TestHardwareShow(TestHardware):
    def setUp(self):
        super().setUp()

        self.hardware_mock.get.return_value = (
            hardware_fakes.FakeHardware.create_one_hardware()
        )

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

        self.hardware_mock.get.assert_called_with(*args)

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

        hw1 = hardware_fakes.FakeHardware.create_one_hardware()
        hw1['workers'].append(
            hardware_fakes.FakeHardware.create_one_worker(
                worker_type="blazar",
                worker_state="PENDING"
            )
        )
        hw1['workers'].append(
            hardware_fakes.FakeHardware.create_one_worker(
                worker_type="ironic",
                worker_state="STEADY"
            )
        )
        hw2 = hardware_fakes.FakeHardware.create_one_hardware()
        hw2['workers'].append(
            hardware_fakes.FakeHardware.create_one_worker(
                worker_type="ironic",
                worker_state="PENDING"
            )
        )
        self.hardware_mock.list.return_value = list([hw1, hw2])
        self.cmd = hardware_cli.ListHardware(self.app, None)

    def test_hardware_list(self):
        arglist = []
        verifylist = []
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        # DisplayCommandBase.take_action() returns two tuples
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(len(data), 2)

        expected_args = []
        self.hardware_mock.list.assert_called_with(*expected_args)

    def test_hardware_list_worker_state_filter(self):
        arglist = ["--worker-state", "PENDING"]
        verifylist = [("worker_state", "PENDING")]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)


        # DisplayCommandBase.take_action() returns two tuples
        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(len(data), 2)

        expected_args = []
        self.hardware_mock.list.assert_called_with(*expected_args)

    def test_hardware_list_worker_type_filter(self):
        # Test with worker type filter
        arglist = ["--worker-type", "ironic"]
        verifylist = [("worker_type", "ironic")]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(len(data), 2)

        expected_args = []
        self.hardware_mock.list.assert_called_with(*expected_args)


    def test_hardware_list_combined_filters(self):
        # Test with both worker type and state filters
        arglist = ["--worker-type", "blazar", "--worker-state", "STEADY"]
        verifylist = [("worker_type", "blazar"), ("worker_state", "STEADY")]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(len(data), 0)

        expected_args = []
        self.hardware_mock.list.assert_called_with(*expected_args)

        arglist = ["--worker-type", "blazar", "--worker-state", "PENDING"]
        verifylist = [("worker_type", "blazar"), ("worker_state", "PENDING")]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)

        columns, data = self.cmd.take_action(parsed_args)
        self.assertEqual(len(data), 1)

        expected_args = []
        self.hardware_mock.list.assert_called_with(*expected_args)


class TestHardwareCreate(TestHardware):
    def setUp(self):
        super().setUp()
        self.cmd = hardware_cli.CreateHardware(self.app, None)


class TestHardwareDelete(TestHardware):
    def setUp(self):
        super().setUp()
        self.cmd = hardware_cli.DeleteHardware(self.app, None)

    def test_hardware_delete_w_same_name(self):
        # When delete when more than two resources exist with same name
        arglist = [FAKE_HARDWARE_NAME]
        verifylist = []
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        # get will throw an Exception when used with name
        self.hardware_mock.get.side_effect = Exception
        self.hardware_mock.find.side_effect = Exception
        # return two hardwares with same name
        self.hardware_mock.list.return_value = [
            hardware_fakes.FakeHardware.create_one_hardware(),
            hardware_fakes.FakeHardware.create_one_hardware()
        ]
        try:
            self.cmd.take_action(parsed_args)
        except exceptions.CommandError as e:
            self.assertEqual(e.args[0], f"More than one resource exists with the name or ID '{FAKE_HARDWARE_NAME}'.")

    def test_hardware_delete_w_name(self):
        arglist = [FAKE_HARDWARE_NAME]
        verifylist = []
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        # get will throw an Exception when used with name
        self.hardware_mock.get.side_effect = Exception
        self.hardware_mock.find.side_effect = Exception
        # return two hardwares with same name
        self.hardware_mock.list.return_value = [
            hardware_fakes.FakeHardware.create_one_hardware()
        ]
        self.cmd.take_action(parsed_args)


    def test_hardware_delete_w_uuid(self):
        arglist = [FAKE_HARDWARE_UUID]
        verifylist = []
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        self.hardware_mock.get.return_value = (
                    hardware_fakes.FakeHardware.create_one_hardware()
                )
        self.cmd.take_action(parsed_args)
        self.hardware_mock.delete.assert_called_with(
            FAKE_HARDWARE_UUID
        )


class TestHardwareSetMeta(type):
    """Metaclass to generate list of test cases."""

    def __new__(mcs, name, bases, dict):
        def gen_test(hw_type, arg, prop, path, value, use_name=False):
            def test(self):

                name_or_id = FAKE_HARDWARE_UUID
                self.hardware_mock.get.return_value = (
                    hardware_fakes.FakeHardware.create_one_hardware()
                )
                self.hardware_mock.update.return_value = (
                    hardware_fakes.FakeHardware.create_one_hardware()
                )
                if use_name:
                    name_or_id = FAKE_HARDWARE_NAME
                    self.hardware_mock.get.side_effect = Exception
                    self.hardware_mock.find.side_effect = Exception
                    self.hardware_mock.list.return_value = [
                        hardware_fakes.FakeHardware.create_one_hardware()
                    ]
                arglist = [
                    name_or_id,
                    "--hardware_type",
                    hw_type,
                    arg,
                    value,
                ]
                parsed_args = self.check_parser(self.cmd, arglist, [])
                assert parsed_args.properties == {prop: value}

                self.cmd.take_action(parsed_args)
                # test if the get is called with name
                self.hardware_mock.get.assert_called_with(name_or_id)
                self.hardware_mock.update.assert_called_with(
                    FAKE_HARDWARE_UUID, [{"op": "add", "path": path, "value": value}]
                )

            return test

        for hw_type, arg, prop, path, value, use_name in UPDATE_PARAMS:
            test_name = "test_device_update_%s" % prop
            dict[test_name] = gen_test(hw_type, arg, prop, path, value, use_name=use_name)
        return type.__new__(mcs, name, bases, dict)


class TestHardwareSet(TestHardware, metaclass=TestHardwareSetMeta):
    def setUp(self):
        super().setUp()
        self.cmd = hardware_cli.UpdateHardware(self.app, None)


class TestHardwareSync(TestHardware):
    def setUp(self):
        super().setUp()
        self.cmd = hardware_cli.SyncHardware(self.app, None)
