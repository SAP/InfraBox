import uuid

from temp_tools import TestClient
from test_template import ApiTestTemplate


class UserGlobalTokensTest(ApiTestTemplate):

    URL = 'api/v1/user/global-tokens'
    TOKEN_URL = URL + '/%s'
    ACCESS_LOG_URL = URL + '/%s/access-log'

    def setUp(self):
        super(UserGlobalTokensTest, self).setUp()

        self.other_user_id = str(uuid.uuid4())
        TestClient.execute("""
            INSERT INTO "user" (id, github_id, username, avatar_url)
            VALUES (%s, 99999, 'other_user', 'url')
        """, [self.other_user_id])

    # ── authorization ──────────────────────────────────────────────────────────

    def test_job_token_is_unauthorized(self):
        r = TestClient.get(self.URL, TestClient.get_job_authorization(self.job_id))
        self.assertEqual(r['message'], 'Unauthorized')

    def test_job_token_cannot_create_token(self):
        r = TestClient.post(self.URL,
                            data={'description': 'x', 'scope_pull': True, 'scope_push': False},
                            headers=TestClient.get_job_authorization(self.job_id))
        self.assertEqual(r['message'], 'Unauthorized')

    # ── list ───────────────────────────────────────────────────────────────────

    def test_list_tokens_initially_empty(self):
        r = TestClient.get(self.URL, TestClient.get_user_authorization(self.user_id))
        self.assertIsInstance(r, list)
        self.assertEqual(len(r), 0)

    def test_list_tokens_only_returns_own_tokens(self):
        # Insert a token owned by another user
        TestClient.execute("""
            INSERT INTO global_token (id, description, scope_push, scope_pull, user_id, expires_at)
            VALUES (%s, 'other token', false, true, %s, NOW() + INTERVAL '30 days')
        """, [str(uuid.uuid4()), self.other_user_id])

        r = TestClient.get(self.URL, TestClient.get_user_authorization(self.user_id))
        self.assertEqual(len(r), 0)

    # ── create ─────────────────────────────────────────────────────────────────

    def test_create_token_returns_jwt(self):
        data = {'description': 'ci-reader', 'scope_pull': True, 'scope_push': False}
        r = TestClient.post(self.URL, data=data,
                            headers=TestClient.get_user_authorization(self.user_id))
        self.assertIn('token', r)
        self.assertIn('id', r)
        self.assertEqual(r['description'], 'ci-reader')
        self.assertTrue(r['scope_pull'])
        self.assertFalse(r['scope_push'])

    def test_create_token_appears_in_list(self):
        data = {'description': 'list-check', 'scope_pull': True, 'scope_push': False}
        TestClient.post(self.URL, data=data,
                        headers=TestClient.get_user_authorization(self.user_id))

        r = TestClient.get(self.URL, TestClient.get_user_authorization(self.user_id))
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]['description'], 'list-check')
        self.assertTrue(r[0]['scope_pull'])
        self.assertFalse(r[0]['scope_push'])
        self.assertIn('created_at', r[0])

    def test_create_token_persists_in_db(self):
        data = {'description': 'db-check', 'scope_pull': True, 'scope_push': True}
        create_r = TestClient.post(self.URL, data=data,
                                   headers=TestClient.get_user_authorization(self.user_id))
        token_id = create_r['id']

        row = TestClient.execute_one("""
            SELECT description, scope_push, scope_pull, user_id
            FROM global_token WHERE id = %s
        """, [token_id])
        self.assertEqual(row['description'], 'db-check')
        self.assertTrue(row['scope_push'])
        self.assertTrue(row['scope_pull'])
        self.assertEqual(str(row['user_id']), self.user_id)

    # ── delete ─────────────────────────────────────────────────────────────────

    def test_delete_own_token(self):
        create_r = TestClient.post(self.URL,
                                   data={'description': 'to-delete', 'scope_pull': True, 'scope_push': False},
                                   headers=TestClient.get_user_authorization(self.user_id))
        token_id = create_r['id']

        r = TestClient.delete(self.TOKEN_URL % token_id,
                              headers=TestClient.get_user_authorization(self.user_id))
        self.assertEqual(r['status'], 200)

        # Verify removed from list
        list_r = TestClient.get(self.URL, TestClient.get_user_authorization(self.user_id))
        ids = [t['id'] for t in list_r]
        self.assertNotIn(token_id, ids)

    def test_delete_own_token_removes_from_db(self):
        create_r = TestClient.post(self.URL,
                                   data={'description': 'db-delete', 'scope_pull': True, 'scope_push': False},
                                   headers=TestClient.get_user_authorization(self.user_id))
        token_id = create_r['id']

        TestClient.delete(self.TOKEN_URL % token_id,
                          headers=TestClient.get_user_authorization(self.user_id))

        count = TestClient.execute_one("SELECT COUNT(*) FROM global_token WHERE id = %s", [token_id])
        self.assertEqual(count[0], 0)

    def test_cannot_delete_other_users_token(self):
        other_token_id = str(uuid.uuid4())
        TestClient.execute("""
            INSERT INTO global_token (id, description, scope_push, scope_pull, user_id, expires_at)
            VALUES (%s, 'not yours', false, true, %s, NOW() + INTERVAL '30 days')
        """, [other_token_id, self.other_user_id])

        r = TestClient.delete(self.TOKEN_URL % other_token_id,
                              headers=TestClient.get_user_authorization(self.user_id))
        self.assertEqual(r['status'], 404)

        # Token still exists in DB
        count = TestClient.execute_one("SELECT COUNT(*) FROM global_token WHERE id = %s",
                                       [other_token_id])
        self.assertEqual(count[0], 1)

    def test_delete_nonexistent_token_returns_404(self):
        fake_id = str(uuid.uuid4())
        r = TestClient.delete(self.TOKEN_URL % fake_id,
                              headers=TestClient.get_user_authorization(self.user_id))
        self.assertEqual(r['status'], 404)

    # ── access log ─────────────────────────────────────────────────────────────

    def test_access_log_empty_initially(self):
        create_r = TestClient.post(self.URL,
                                   data={'description': 'log-test', 'scope_pull': True, 'scope_push': False},
                                   headers=TestClient.get_user_authorization(self.user_id))
        token_id = create_r['id']

        r = TestClient.get(self.ACCESS_LOG_URL % token_id,
                           headers=TestClient.get_user_authorization(self.user_id))
        self.assertIsInstance(r, list)
        self.assertEqual(len(r), 0)

    def test_access_log_returns_entries(self):
        create_r = TestClient.post(self.URL,
                                   data={'description': 'log-entries', 'scope_pull': True, 'scope_push': False},
                                   headers=TestClient.get_user_authorization(self.user_id))
        token_id = create_r['id']

        TestClient.execute("""
            INSERT INTO global_token_access_log (token_id, path, method, status_code)
            VALUES (%s, '/api/v1/projects', 'GET', 200)
        """, [token_id])
        TestClient.execute("""
            INSERT INTO global_token_access_log (token_id, path, method, status_code)
            VALUES (%s, '/api/v1/projects/abc/builds', 'GET', 200)
        """, [token_id])

        r = TestClient.get(self.ACCESS_LOG_URL % token_id,
                           headers=TestClient.get_user_authorization(self.user_id))
        self.assertEqual(len(r), 2)
        paths = {e['path'] for e in r}
        self.assertIn('/api/v1/projects', paths)
        self.assertIn('/api/v1/projects/abc/builds', paths)
        for entry in r:
            self.assertIn('accessed_at', entry)
            self.assertIn('method', entry)
            self.assertIn('status_code', entry)

    def test_access_log_enforces_ownership(self):
        other_token_id = str(uuid.uuid4())
        TestClient.execute("""
            INSERT INTO global_token (id, description, scope_push, scope_pull, user_id, expires_at)
            VALUES (%s, 'other log token', false, true, %s, NOW() + INTERVAL '30 days')
        """, [other_token_id, self.other_user_id])
        TestClient.execute("""
            INSERT INTO global_token_access_log (token_id, path, method, status_code)
            VALUES (%s, '/api/v1/projects', 'GET', 200)
        """, [other_token_id])

        r = TestClient.get(self.ACCESS_LOG_URL % other_token_id,
                           headers=TestClient.get_user_authorization(self.user_id))
        self.assertEqual(r['status'], 404)

    def test_access_log_nonexistent_token_returns_404(self):
        fake_id = str(uuid.uuid4())
        r = TestClient.get(self.ACCESS_LOG_URL % fake_id,
                           headers=TestClient.get_user_authorization(self.user_id))
        self.assertEqual(r['status'], 404)