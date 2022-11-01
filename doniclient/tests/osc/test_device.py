from doniclient.osc import device
from doniclient.tests.osc import common, fakes

FAKE_HARDWARE_UUID = fakes.hardware_uuid


UPDATE_PARAMS = [
        ("--machine-name","machine_name","/properties/machine_name","jetson-nano"),
        ("--contact-email","contact_email","/properties/contact_email","test@foo.bar"),
        ("--local-egress","local_egress","/properties/local_egress","allow"),
    ]



class TestCreate(common.TestHardware):
    def setUp(self):
        super().setUp()
        self.cmd = device.CreateDevice(self.app, None)



class TestSetMeta(type):
    def __new__(mcs, name, bases, dict):
        def gen_test(arg,prop,path,value):
            def test(self):
                self.hardware_mock.update.return_value = fakes.FakeHardware.create_one_hardware()
                arglist = [FAKE_HARDWARE_UUID, arg, value]
                parsed_args = self.check_parser(self.cmd, arglist, [])
                assert parsed_args.properties == {prop: value}

                self.cmd.take_action(parsed_args)
                self.hardware_mock.update.assert_called_with(FAKE_HARDWARE_UUID, [{
                    "op": "add", "path": path, "value": value
                }])
            return test

        for arg,prop,path,value in UPDATE_PARAMS:
            test_name = "test_device_update_%s" % prop
            dict[test_name] = gen_test(arg,prop,path,value)
        return type.__new__(mcs, name, bases, dict)



class TestDeviceSet(common.TestHardware, metaclass=TestSetMeta):
    def setUp(self):
        super().setUp()
        self.cmd = device.UpdateDevice(self.app, None)
