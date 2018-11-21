from temp_tools import TestClient
from test_template import ApiTestTemplate

from quotas import *

from pyinfraboxutils import get_logger
from time import sleep
logger = get_logger('api')

class QuotasTest(ApiTestTemplate):

    url_ns = 'api/job'

    def setUp(self):
        super(QuotasTest, self).setUp()
        self.test_secret_data = {'name': 'Test_secret_',
                                 'value': 'JFPOIEHEBLJSFUGFSUYDWGFSDBUWFGDSLKFGWYFGSDJ'}


    
    def test_quotas_add_secret_froze(self):
        '''
        #Set secret quota value to 0
        secretQuotaValue = TestClient.get('api/v1/admin/quotas/name/max_secret_project', 
                                            headers=TestClient.get_user_authorization(self.admin_id))['value']

        for i in range(0, secretQuotaValue):
            tmp_data = dict(self.test_secret_data)
            tmp_data['name'] += str(i)

            # test secret creation
            r = TestClient.post('api/v1/projects/%s/secrets/' % self.project_id, data=tmp_data,
                                headers=TestClient.get_user_authorization(self.user_id))
            self.assertEqual(r['message'], 'Successfully added secret.')
            self.assertEqual(r['status'], 200)


        #Test adding new secret
        r = TestClient.post('api/v1/projects/%s/secrets/' % self.project_id, data=self.test_secret_data, headers=TestClient.get_user_authorization(self.user_id))
        self.assertEqual(r['message'], 'Too many secrets by quotas.')
        '''
        pass

    def test_quotas_add_secret(self):

        #Set secret quota value to 0
        secretQuotaValueID = TestClient.get('api/v1/admin/quotas/name/max_secret_project', 
                                            headers=TestClient.get_user_authorization(self.admin_id))['id']
        dataQuota = {'value': 0, 'description': ''}
        TestClient.post('api/v1/admin/quota/%s' % secretQuotaValueID, data=dataQuota, headers=TestClient.get_user_authorization(self.admin_id))

        #Test adding new secret
        r = TestClient.post('api/v1/projects/%s/secrets/' % self.project_id, data=self.test_secret_data, headers=TestClient.get_user_authorization(self.user_id))
        self.assertEqual(r['message'], 'Too many secrets by quotas.')

    def test_quota_add_job(self):

        #Check CPU quota
        cpuQuotaValue = TestClient.get('api/v1/admin/quotas/name/max_cpu_job', 
                                            headers=TestClient.get_user_authorization(self.admin_id))['value']

        memoryQuotaValue = TestClient.get('api/v1/admin/quotas/name/max_cpu_job', 
                                            headers=TestClient.get_user_authorization(self.admin_id))['value']

        timeoutQuotaValue = TestClient.get('api/v1/admin/quotas/name/max_cpu_job', 
                                            headers=TestClient.get_user_authorization(self.admin_id))['value']

        job_id = "6544af82-1c4f-5bb5-b1da-a54a0ced5e6f"
        data = {"jobs": [{
            "id": job_id,
            "type": "docker",
            "name": "test_job1",
            "docker_file": "",
            "build_only": False,
            "resources": {"limits": {"cpu": cpuQuotaValue, "memory": memoryQuotaValue-1}}
        }]}
        r = TestClient.post(self.url_ns + '/create_jobs', data, self.job_headers)
        self.assertEqual(r['message'], 'Too many CPU for a job by quotas.')


        job_id = "6544af82-1c4f-5bb5-b1da-a54a0ced5e6f"
        data = {"jobs": [{
            "id": job_id,
            "type": "docker",
            "name": "test_job1",
            "docker_file": "",
            "build_only": False,
            "resources": {"limits": {"cpu": cpuQuotaValue-1, "memory": memoryQuotaValue-1}}
        }]}
        r = TestClient.post(self.url_ns + '/create_jobs', data, self.job_headers)
        self.assertEqual(r, 'Successfully create jobs')

        #Check Timeout quota
        '''
        job_id = "6544af82-1c4f-5bb5-b1da-a54a0ced5e6g"
        data = {"jobs": [{
            "id": job_id,
            "type": "docker",
            "name": "test_job2",
            "docker_file": "",
            "build_only": False,
            "resources": {"limits": {"cpu": cpuQuotaValue-1, "memory": memoryQuotaValue-1}},
            "timeout": timeoutQuotaValue
        }]}
        r = TestClient.post(self.url_ns + '/create_jobs', data, self.job_headers)
        self.assertEqual(r['message'], 'Too many timeout for a job by quotas.')


        job_id = "6544af82-1c4f-5bb5-b1da-a54a0ced5e6g"
        data = {"jobs": [{
            "id": job_id,
            "type": "docker",
            "name": "test_job2",
            "docker_file": "",
            "build_only": False,
            "resources": {"limits": {"cpu": cpuQuotaValue-1, "memory": memoryQuotaValue-1}},
            "timeout": timeoutQuotaValue-1
        }]}
        r = TestClient.post(self.url_ns + '/create_jobs', data, self.job_headers)
        self.assertEqual(r, 'Successfully create jobs')
        '''

