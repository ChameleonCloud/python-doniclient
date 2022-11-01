from doniclient.osc import cli as hardware_cli
from doniclient.tests.osc import fakes as hardware_fakes

FAKE_HARDWARE_UUID = hardware_fakes.hardware_uuid

class TestHardware(hardware_fakes.TestHardware):
    def setUp(self):
        super(TestHardware, self).setUp()

        # Get a shortcut to the baremetal manager mock
        self.hardware_mock = self.app.client_manager.inventory
        self.hardware_mock.reset_mock()
