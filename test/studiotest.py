import urllib2
import unittest
import mox
from mox import IsA

import studioapi


class StudioTest(mox.MoxTestBase):
    def __init__(self, methodName):
        mox.MoxTestBase.__init__(self, methodName)
        self.resdir = '/home/chorler/projects/src/PySUSEStudio/test/responses'

    def setUp(self):
        mox.MoxTestBase.setUp(self)
        self.connection = studioapi.BaseConnection(
            'http://www.nostudio.com', 'api/v1')
        self.studio = studioapi.StudioAPI(self.connection)
                                            
    def test_get_api_key(self):
        f = urllib2.urlopen('file://%s/api_version.xml' % self.resdir)
        self.mox.StubOutWithMock(urllib2, 'urlopen')
        self.mox.StubOutClassWithMocks(studioapi, 'HTTPGetRequest')
        mockreq = studioapi.HTTPGetRequest(IsA(basestring))
        urllib2.urlopen(mockreq).AndReturn(f)
        self.mox.ReplayAll()
        self.studio.get_api_key()
        self.mox.VerifyAll()

    #def test_get_account(self):
    #def test_get_api_version(self):
    #def test_get_template_sets(self):
    #def test_get_appliances(self):
    #def test_get_appliance_status(self):
    #def test_create_appliance(self):
    #def test_delete_appliance(self):
    #def test_get_appliance_repositories(self):
    #def test_add_appliance_repositories(self):
    #def test_add_appliance_repository(self):
    #def test_remove_appliance_repository(self):
    #def test_add_appliance_user_repository(self):
    #def test_get_appliance_software(self):
    #def test_set_appliance_software(self):
    #def test_get_appliance_installed_software(self):
    #def test_add_appliance_software_package(self):
    #def test_remove_appliance_software_package(self):
    #def test_add_appliance_software_pattern(self):
    #def test_remove_appliance_software_pattern(self):
    #def test_ban_appliance_software_package(self):
    #def test_unban_appliance_software_package(self):
    #def test_search_appliance_software(self):
    #def test_get_appliance_image_file(self):
    #def test_get_appliance_gpg_keys(self):
    #def test_get_appliance_gpg_key(self):
    #def test_upload_appliance_gpg_key(self):
    #def test_delete_appliance_gpg_key(self):
    #def test_get_appliance_overlay_files(self):
    #def test_add_appliance_overlay_file(self):
    #def test_get_overlay_file(self):
    #def test_add_overlay_file(self):
    #def test_get_overlay_file_metadata(self):
    #def test_add_overlay_file_metadata(self):
    #def test_delete_overlay_file(self):
    #def test_get_running_appliance_builds(self):
    #def test_get_build_status(self):
    #def test_add_build(self):
    #def test_cancel_build(self):
    #def test_get_completed_builds(self):
    #def test_get_build_info(self):
    #def test_delete_build(self):
    #def test_get_base_system_rpms(self):
    #def test_get_rpm_info(self):
    #def test_get_rpm(self):
    #def test_upload_rpm(self):
    #def test_update_rpm(self):
    #def test_delete_rpm(self):
    #def test_get_repositories(self):
    #def test_import_repository(self):
    #def test_get_repository_info(self):
    #def test_get_testdrives(self):
    #def test_start_testdrive(self):
    #def test_version(self):



if __name__ == '__main__':
    unittest.main()

