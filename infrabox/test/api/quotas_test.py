from temp_tools import TestClient
from test_template import ApiTestTemplate

from quotas import *

from pyinfraboxutils import get_logger
from time import sleep
logger = get_logger('api')

class QuotasTest(ApiTestTemplate):

    def setUp(self):
        super(QuotasTest, self).setUp()
        self.test_secret_data = {'name': 'Test_secret_',
                                 'value': 'JFPOIEHEBLJSFUGFSUYDWGFSDBUWFGDSLKFGWYFGSDJ'}
    
    def test_quotas_add_secret(self):

        #Set secret quota value to 0
        secretQuotaValueID = TestClient.get('api/v1/admin/quotas/name/max_secret_project', 
                                            headers=TestClient.get_user_authorization(self.admin_id))['id']
        dataQuota = {'value': 0, 'description': ''}
        TestClient.post('api/v1/admin/quota/%s' % secretQuotaValueID, data=dataQuota, headers=TestClient.get_user_authorization(self.admin_id))

        #Test adding new secret
        r = TestClient.post('api/v1/projects/%s/secrets/' % self.project_id, data=self.test_secret_data, headers=TestClient.get_user_authorization(self.user_id))
        self.assertEqual(r['message'], 'Too many secrets by quotas.')
