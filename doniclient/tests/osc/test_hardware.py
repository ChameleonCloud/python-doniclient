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




update_params = [
        ("--mgmt_addr","mgmt_addr","/properties/mgmt_addr","fake-mgmt_addr"),
        ("--local-egress","local_egress","/properties/local_egress","allow"),
    ]

class TestHardwareSetSequenceMeta(type):
    def __new__(mcs, name, bases, dict):
        def gen_test(arg,prop,path,value):
            def test(self):
                self.hardware_mock.update.return_value = hardware_fakes.FakeHardware.create_one_hardware()
                arglist = [FAKE_HARDWARE_UUID, arg, value]
                parsed_args = self.check_parser(self.cmd, arglist, [])
                assert parsed_args.properties == {prop: value}

                self.cmd.take_action(parsed_args)
                self.hardware_mock.update.assert_called_with(FAKE_HARDWARE_UUID, [{
                    "op": "add", "path": path, "value": value
                }])
            return test

        for arg,prop,path,value in update_params:
            test_name = "test_hardware_update_%s" % prop
            dict[test_name] = gen_test(arg,prop,path,value)
        return type.__new__(mcs, name, bases, dict)



class TestHardwareSetSequence(TestHardware, metaclass=TestHardwareSetSequenceMeta):
    def setUp(self):
        super().setUp()
        self.cmd = hardware_cli.UpdateHardware(self.app, None)

class TestHardwareSync(TestHardware):
    def setUp(self):
        super().setUp()
        self.cmd = hardware_cli.SyncHardware(self.app, None)
