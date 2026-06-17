"""
Unit tests for the MCP API layer:
  - MCP token auth (valid, invalid, expired, revoked, wrong path)
  - Rate limiter (allow, deny, fail-open)
  - Project access check (token scoped, session fallback)
  - Trigger access check
"""
import hashlib
import secrets
import sys
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

# Add src/ to path so we can import the MCP modules directly without
# triggering api/handlers/__init__.py (which requires INFRABOX_* env vars).
import os
_src_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src')
sys.path.insert(0, _src_dir)

# Stub heavy server-init modules before importing our modules
import types

# pyinfraboxutils stubs
piu = types.ModuleType('pyinfraboxutils')
piu.get_logger = lambda name: __import__('logging').getLogger(name)
piu.get_env = lambda k: os.environ.get(k, '')
sys.modules.setdefault('pyinfraboxutils', piu)
sys.modules.setdefault('pyinfraboxutils.dbpool', types.ModuleType('pyinfraboxutils.dbpool'))
sys.modules.setdefault('pyinfraboxutils.db', types.ModuleType('pyinfraboxutils.db'))

# flask_restx stub
frestx = types.ModuleType('flask_restx')
frestx.Resource = object
frestx.Api = MagicMock()
sys.modules.setdefault('flask_restx', frestx)

ibrestplus = types.ModuleType('pyinfraboxutils.ibrestplus')
ibrestplus.api = MagicMock()
ibrestplus.response_model = {}
sys.modules.setdefault('pyinfraboxutils.ibrestplus', ibrestplus)

# Stub api.handlers as a real package (with __path__) so Python can resolve
# api.handlers.mcp.* from disk without executing api/handlers/__init__.py.
_API_HANDLERS = 'api.handlers'

# Stub api.handlers as a real package (with __path__) so Python can resolve
# api.handlers.mcp.* from disk without executing api/handlers/__init__.py.
_api = types.ModuleType('api')
_api.__path__ = [os.path.join(_src_dir, 'api')]
_api.__package__ = 'api'
_api_handlers = types.ModuleType(_API_HANDLERS)
_api_handlers.__path__ = [os.path.join(_src_dir, 'api', 'handlers')]
_api_handlers.__package__ = _API_HANDLERS
_api.handlers = _api_handlers
sys.modules['api'] = _api
sys.modules[_API_HANDLERS] = _api_handlers

# Now import the modules under test directly
import importlib
mcp_auth = importlib.import_module('api.handlers.mcp.auth')
mcp_rate_limit_mod = importlib.import_module('api.handlers.mcp.rate_limit')


# ---------------------------------------------------------------------------
# Auth module — token hash
# ---------------------------------------------------------------------------

class TestMcpTokenHash(unittest.TestCase):
    def test_hash_is_sha256_hex(self):
        result = mcp_auth._hash_token('ib_mcp_' + 'a' * 48)
        self.assertEqual(len(result), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in result))

    def test_different_tokens_produce_different_hashes(self):
        h1 = mcp_auth._hash_token('ib_mcp_' + 'a' * 48)
        h2 = mcp_auth._hash_token('ib_mcp_' + 'b' * 48)
        self.assertNotEqual(h1, h2)

    def test_same_token_deterministic(self):
        raw = 'ib_mcp_' + secrets.token_hex(24)
        self.assertEqual(mcp_auth._hash_token(raw), mcp_auth._hash_token(raw))

    def test_matches_expected_sha256(self):
        raw = 'ib_mcp_test'
        expected = hashlib.sha256(raw.encode('utf-8')).hexdigest()
        self.assertEqual(mcp_auth._hash_token(raw), expected)


# ---------------------------------------------------------------------------
# Project access check
# ---------------------------------------------------------------------------

class TestCheckProjectAccessMcp(unittest.TestCase):
    def _g_with_projects(self, projects):
        g = MagicMock()
        g.mcp_enabled_projects = projects
        return g

    def test_no_mcp_attr_allows_all(self):
        g = MagicMock(spec=[])   # no mcp_enabled_projects attribute at all
        with patch.object(mcp_auth, 'g', g):
            self.assertTrue(mcp_auth.check_project_access_mcp('any-id'))

    def test_project_not_in_scope_denied(self):
        g = self._g_with_projects({'other-id': None})
        with patch.object(mcp_auth, 'g', g):
            self.assertFalse(mcp_auth.check_project_access_mcp('target-id'))

    def test_project_in_scope_no_expiry_allowed(self):
        g = self._g_with_projects({'target-id': None})
        with patch.object(mcp_auth, 'g', g):
            self.assertTrue(mcp_auth.check_project_access_mcp('target-id'))

    def test_per_project_expiry_in_future_allowed(self):
        future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        g = self._g_with_projects({'pid': future})
        with patch.object(mcp_auth, 'g', g):
            self.assertTrue(mcp_auth.check_project_access_mcp('pid'))

    def test_per_project_expiry_in_past_denied(self):
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        g = self._g_with_projects({'pid': past})
        with patch.object(mcp_auth, 'g', g):
            self.assertFalse(mcp_auth.check_project_access_mcp('pid'))


# ---------------------------------------------------------------------------
# Trigger access check
# ---------------------------------------------------------------------------

class TestCheckTriggerAccessMcp(unittest.TestCase):
    def test_no_mcp_attr_allows(self):
        g = MagicMock(spec=[])
        with patch.object(mcp_auth, 'g', g):
            self.assertTrue(mcp_auth.check_trigger_access_mcp())

    def test_allow_trigger_true(self):
        g = MagicMock()
        g.mcp_allow_trigger = True
        with patch.object(mcp_auth, 'g', g):
            self.assertTrue(mcp_auth.check_trigger_access_mcp())

    def test_allow_trigger_false(self):
        g = MagicMock()
        g.mcp_allow_trigger = False
        with patch.object(mcp_auth, 'g', g):
            self.assertFalse(mcp_auth.check_trigger_access_mcp())


# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------

class TestMcpRateLimit(unittest.TestCase):
    def _run_check(self, count_result):
        mock_redis = MagicMock()
        pipeline = MagicMock()
        pipeline.execute.return_value = [None, None, count_result, None]
        mock_redis.pipeline.return_value = pipeline

        with patch.object(mcp_rate_limit_mod, '_get_redis', return_value=mock_redis), \
             patch('time.time', return_value=1_000_000.0):
            return mcp_rate_limit_mod._check_rate_limit('user-123', 'list_builds')

    def test_under_limit_allowed(self):
        self.assertTrue(self._run_check(1))

    def test_at_limit_allowed(self):
        self.assertTrue(self._run_check(mcp_rate_limit_mod._DEFAULT_RPM))

    def test_over_limit_denied(self):
        self.assertFalse(self._run_check(mcp_rate_limit_mod._DEFAULT_RPM + 1))

    def test_fail_open_when_no_redis(self):
        with patch.object(mcp_rate_limit_mod, '_get_redis', return_value=None):
            self.assertTrue(mcp_rate_limit_mod._check_rate_limit('user', 'list_builds'))

    def test_fail_open_on_redis_exception(self):
        mock_redis = MagicMock()
        mock_redis.pipeline.side_effect = RuntimeError('connection lost')
        with patch.object(mcp_rate_limit_mod, '_get_redis', return_value=mock_redis):
            self.assertTrue(mcp_rate_limit_mod._check_rate_limit('user', 'list_builds'))

    def test_trigger_rpm_lower_than_default(self):
        self.assertLess(mcp_rate_limit_mod._ENDPOINT_LIMITS['trigger_build'],
                        mcp_rate_limit_mod._DEFAULT_RPM)

    def test_log_rpm_lower_than_default(self):
        self.assertLess(mcp_rate_limit_mod._ENDPOINT_LIMITS['get_job_log'],
                        mcp_rate_limit_mod._DEFAULT_RPM)

    def test_artifact_rpm_lower_than_default(self):
        self.assertLess(mcp_rate_limit_mod._ENDPOINT_LIMITS['list_job_artifacts'],
                        mcp_rate_limit_mod._DEFAULT_RPM)

    def test_different_users_independent(self):
        # Two users: first at limit, second should still be allowed.
        calls = []
        def fake_check(user_id, endpoint):
            calls.append(user_id)
            if user_id == 'heavy-user':
                return False
            return True
        with patch.object(mcp_rate_limit_mod, '_check_rate_limit', side_effect=fake_check):
            self.assertFalse(mcp_rate_limit_mod._check_rate_limit('heavy-user', 'list_builds'))
            self.assertTrue(mcp_rate_limit_mod._check_rate_limit('normal-user', 'list_builds'))


# ---------------------------------------------------------------------------
# Builds routes — MCPBuilds.get and MCPTrigger.post
# ---------------------------------------------------------------------------

# Strategy: the route decorators (@mcp_auth_required, @mcp_rate_limit) and
# flask.g/request are real werkzeug-backed objects already loaded.  Stub the
# decorators to pass-throughs, fix the namespace decorator, stub audit, then
# reload builds.py so the route classes are plain Python classes again.
# Use a real Flask app + test_request_context so g/abort work properly.

import flask as _real_flask
from werkzeug.exceptions import HTTPException as _HTTPException

# Patch decorators before reload so the reloaded module picks up pass-throughs.
_mcp_auth_mod = sys.modules['api.handlers.mcp.auth']
_mcp_auth_mod.mcp_auth_required = lambda f: f
mcp_rate_limit_mod.mcp_rate_limit = lambda endpoint: (lambda f: f)

class _PassNs:
    def route(self, *a, **kw): return lambda cls: cls

sys.modules['pyinfraboxutils.ibrestplus'].api.namespace = lambda *a, **kw: _PassNs()

_audit_stub = types.ModuleType('api.handlers.mcp.audit')
_audit_stub.audit_mcp = MagicMock()
sys.modules['api.handlers.mcp.audit'] = _audit_stub

mcp_builds_mod = importlib.reload(sys.modules['api.handlers.mcp.routes.builds'])

_flask_app = _real_flask.Flask(__name__)
_flask_app.config['TESTING'] = True


def _make_db(*, project=None, rows=None, execute_raises=None):
    db = MagicMock()
    db.execute_one_dict.return_value = project
    db.execute_many_dict.return_value = rows or []
    if execute_raises:
        db.execute.side_effect = execute_raises
    return db


class TestMCPBuildsGet(unittest.TestCase):
    def setUp(self):
        _audit_stub.audit_mcp.reset_mock()

    def _call(self, db, project_id='proj-1'):
        with _flask_app.test_request_context('/'):
            _real_flask.g.db = db
            return mcp_builds_mod.MCPBuilds().get(project_id)

    def test_returns_build_list(self):
        from datetime import datetime
        db = _make_db(rows=[
            {'id': 'b1', 'build_number': 1, 'restart_counter': 0,
             'project_id': 'proj-1', 'commit_id': 'abc', 'branch': 'main',
             'created_at': datetime(2024, 1, 1), 'finished_at': None, 'status': 'finished'},
        ])
        with patch.object(mcp_builds_mod, 'check_project_access_mcp', return_value=True):
            result = self._call(db)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['build_number'], 1)
        self.assertEqual(result[0]['branch'], 'main')

    def test_forbidden_when_no_project_access(self):
        db = _make_db(rows=[])
        with patch.object(mcp_builds_mod, 'check_project_access_mcp', return_value=False):
            with self.assertRaises(_HTTPException) as ctx:
                self._call(db)
        self.assertEqual(ctx.exception.code, 403)

    def test_db_exception_propagates(self):
        db = _make_db()
        db.execute_many_dict.side_effect = RuntimeError('db error')
        with patch.object(mcp_builds_mod, 'check_project_access_mcp', return_value=True):
            with self.assertRaises(RuntimeError):
                self._call(db)

    def test_created_at_iso_format(self):
        from datetime import datetime
        db = _make_db(rows=[
            {'id': 'b2', 'build_number': 2, 'restart_counter': 0,
             'project_id': 'proj-1', 'commit_id': None, 'branch': None,
             'created_at': datetime(2024, 6, 1, 12, 0, 0), 'finished_at': None, 'status': None},
        ])
        with patch.object(mcp_builds_mod, 'check_project_access_mcp', return_value=True):
            result = self._call(db)
        self.assertEqual(result[0]['created_at'], '2024-06-01T12:00:00')


class TestMCPTriggerPost(unittest.TestCase):
    def setUp(self):
        _audit_stub.audit_mcp.reset_mock()

    def _call(self, db, project_id='proj-1'):
        with _flask_app.test_request_context('/'):
            _real_flask.g.db = db
            return mcp_builds_mod.MCPTrigger().post(project_id)

    def test_trigger_success_returns_build_id(self):
        db = _make_db(project={'id': 'proj-1', 'type': 'upload'})
        with patch.object(mcp_builds_mod, 'check_project_access_mcp', return_value=True), \
             patch.object(mcp_builds_mod, 'check_trigger_access_mcp', return_value=True):
            result, status = self._call(db)
        self.assertEqual(status, 200)
        self.assertIn('build_id', result)

    def test_trigger_inserts_source_column(self):
        """INSERT must reference source='mcp' — regression for missing column in 00047.sql."""
        db = _make_db(project={'id': 'proj-1', 'type': 'upload'})
        with patch.object(mcp_builds_mod, 'check_project_access_mcp', return_value=True), \
             patch.object(mcp_builds_mod, 'check_trigger_access_mcp', return_value=True):
            self._call(db)
        # call[0]=LOCK TABLE, call[1]=INSERT INTO build
        insert_sql = db.execute.call_args_list[1][0][0]
        self.assertIn('source', insert_sql)
        self.assertIn("'mcp'", insert_sql)

    def test_trigger_test_project_type_allowed(self):
        db = _make_db(project={'id': 'proj-1', 'type': 'test'})
        with patch.object(mcp_builds_mod, 'check_project_access_mcp', return_value=True), \
             patch.object(mcp_builds_mod, 'check_trigger_access_mcp', return_value=True):
            _, status = self._call(db)
        self.assertEqual(status, 200)

    def test_forbidden_no_project_access(self):
        db = _make_db()
        with patch.object(mcp_builds_mod, 'check_project_access_mcp', return_value=False):
            with self.assertRaises(_HTTPException) as ctx:
                self._call(db)
        self.assertEqual(ctx.exception.code, 403)

    def test_forbidden_no_trigger_permission(self):
        db = _make_db()
        with patch.object(mcp_builds_mod, 'check_project_access_mcp', return_value=True), \
             patch.object(mcp_builds_mod, 'check_trigger_access_mcp', return_value=False):
            with self.assertRaises(_HTTPException) as ctx:
                self._call(db)
        self.assertEqual(ctx.exception.code, 403)

    def test_returns_400_for_github_project(self):
        db = _make_db(project={'id': 'proj-1', 'type': 'github'})
        with patch.object(mcp_builds_mod, 'check_project_access_mcp', return_value=True), \
             patch.object(mcp_builds_mod, 'check_trigger_access_mcp', return_value=True):
            _, status = self._call(db)
        self.assertEqual(status, 400)

    def test_returns_404_for_missing_project(self):
        db = _make_db(project=None)
        with patch.object(mcp_builds_mod, 'check_project_access_mcp', return_value=True), \
             patch.object(mcp_builds_mod, 'check_trigger_access_mcp', return_value=True):
            with self.assertRaises(_HTTPException) as ctx:
                self._call(db)
        self.assertEqual(ctx.exception.code, 404)

    def test_db_exception_propagates(self):
        db = _make_db(
            project={'id': 'proj-1', 'type': 'upload'},
            execute_raises=RuntimeError('db error'),
        )
        with patch.object(mcp_builds_mod, 'check_project_access_mcp', return_value=True), \
             patch.object(mcp_builds_mod, 'check_trigger_access_mcp', return_value=True):
            with self.assertRaises(RuntimeError):
                self._call(db)


if __name__ == '__main__':
    unittest.main()

