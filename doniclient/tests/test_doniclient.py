import copy
import uuid
from unittest import mock

from openstackclient.tests.unit import fakes, utils

from doniclient import __version__, hardware


def test_version():
    assert __version__ == "0.1.0"


class FakeHardware(object):
    @staticmethod
    def create_one_hardware(attrs=None):
        """Create a fake hw item."""
        attrs = attrs or {}

        hw_info = {
            "id": 1,
            "uuid": uuid.uuid4().hex,
            "hardware_type": "PhysicalHost",
            "project_id": uuid.uuid4().hex,
            "name": uuid.uuid4().hex,
            "properties": {},
        }

        hw_info.update(attrs)

        hw_item = fakes.FakeResource(info=copy.deepcopy(hw_info), loaded=True)
        return hw_item


class FakeHardwareClient(object):
    def __init__(self, **kwargs) -> None:
        self.hardware = mock.Mock()
        self.hardware.resource_class = fakes.FakeResource(None, {})


class TestHardware(utils.TestCommand):
    def setUp(self):
        super(TestHardware, self).setUp()

        self.app.client_manager.inventory = FakeHardwareClient(
            endpoint=fakes.AUTH_URL, token=fakes.AUTH_TOKEN
        )

        # Get a shortcut to the Hardware Mock
        self.app.client_manager.sdk_connection = mock.Mock()
        self.app.client_manager.sdk_connection.inventory = mock.Mock()
        self.sdk_client = self.app.client_manager.sdk_connection.inventory


class TestHardwareCreate(TestHardware):
    def setUp(self):
        super(TestHardwareCreate, self).setUp()
        self.cmd = hardware.Create(self.app, None)

    fake_hw = FakeHardware.create_one_hardware()

    def test_one(self):
        pass


class TestHardwareList(TestHardware):
    def setUp(self):
        super(TestHardwareList, self).setUp()
        self.cmd = hardware.List(self.app, None)

    fake_hw = FakeHardware.create_one_hardware()

    def test_one(self):
        pass


# class TestHardwareExport(TestHardware):
#     def setUp(self):
#         super(TestHardwareExport, self).setUp()
#         self.cmd = hardware.ExportResources(self.app, None)

#     fake_hw = FakeHardware.create_one_hardware()

#     def test_hardware_export(self):
#         pass


# class TestHardwareGet(TestHardware):
#     def setUp(self):
#         super(TestHardwareGet, self).setUp()
#         self.cmd = hardware.GetResource(self.app, None)

#     fake_hw = FakeHardware.create_one_hardware()

#     def test_hardware_get(self):
#         self.cmd.take_action([])


# class TestHardwareUpdate(TestHardware):
#     def setUp(self):
#         super(TestHardwareUpdate, self).setUp()
#         self.cmd = hardware.UpdateResource(self.app, None)

#     fake_hw = FakeHardware.create_one_hardware()

#     def test_hardware_update(self):
#         pass


# class TestHardwareSync(TestHardware):
#     def setUp(self):
#         super(TestHardwareSync, self).setUp()
#         self.cmd = hardware.SyncResource(self.app, None)

#     fake_hw = FakeHardware.create_one_hardware()

#     def test_hardware_sync(self):
#         pass
