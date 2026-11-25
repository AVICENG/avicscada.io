import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

from avic_core.audit.service import AuditService
from avic_core.security.auth import SecurityManager
from avic_core.security.fastapi_adapter import (
    AVICSecurityMiddleware, HttpSecurityConfig, authorized_operation,
    clear_session_cookie, set_session_cookie, security_gateway_protected,
    validate_security_routes, UnprotectedRouteError,
)
from avic_core.security.gateway import Operation, SecurityGateway
from avic_core.security.rbac import Scope


class FastAPISecurityAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.security = SecurityManager(root / 'security.db')
        self.audit = AuditService(root / 'audit.db')
        self.security.bootstrap_admin('rootadmin', 'StrongPassword123')
        self.session = self.security.login('rootadmin', 'StrongPassword123')
        self.gateway = SecurityGateway(self.security, self.audit)
        self.config = HttpSecurityConfig(
            allowed_origins=frozenset({'http://testserver'}), https_required=False,
            allow_loopback_http=True, cookie_secure=False, rate_limit_requests=2,
            rate_limit_window_seconds=60,
        )
        self.app = FastAPI()
        self.app.add_middleware(AVICSecurityMiddleware, config=self.config)
        op = Operation('station.start', Scope.STATION, 'station', 'station-1',
                       station_id='station-1', mutating=True)
        secured = authorized_operation(self.gateway, op)

        @self.app.post('/station/start')
        @security_gateway_protected
        def start_station(authorization=secured):
            return {'result': authorization.execute(lambda: {'state': 'started'})}

        @self.app.post('/auth/login')
        def login(response: Response):
            from avic_core.security.fastapi_adapter import set_session_cookie
            data = set_session_cookie(response, self.session, self.config)
            return data

        @self.app.post('/auth/logout')
        def logout(response: Response):
            clear_session_cookie(response, self.config)
            return {'ok': True}

        self.client = TestClient(self.app)

    def tearDown(self):
        self.tmp.cleanup()

    def test_mutation_requires_session_and_csrf_and_audits(self):
        no_session = self.client.post('/station/start', headers={'Origin': 'http://testserver'})
        self.assertEqual(no_session.status_code, 401)
        no_csrf = self.client.post('/station/start', headers={'Origin': 'http://testserver', 'Cookie': f'avic_session={self.session.token}'})
        self.assertEqual(no_csrf.status_code, 401)
        ok = self.client.post('/station/start', headers={'Origin': 'http://testserver', 'X-AVIC-CSRF': self.session.csrf_token,
                                       'Cookie': f'avic_session={self.session.token}'})
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.json()['result']['state'], 'started')
        self.assertEqual(self.audit.verify_chain(), (True, 1))

    def test_origin_is_enforced(self):
        response = self.client.post('/station/start', headers={'Origin': 'https://evil.example'})
        self.assertEqual(response.status_code, 403)
        missing = self.client.post('/station/start')
        self.assertEqual(missing.status_code, 403)

    def test_production_cookie_configuration_fails_closed(self):
        with self.assertRaises(ValueError):
            HttpSecurityConfig(allowed_origins=frozenset({'https://scada.example'}),
                               https_required=True, cookie_secure=False)
        with self.assertRaises(ValueError):
            HttpSecurityConfig(allowed_origins=frozenset({'http://scada.example'}),
                               https_required=True, cookie_secure=True)

    def test_security_headers_added(self):
        response = self.client.post('/auth/login', headers={'Origin': 'http://testserver'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['x-content-type-options'], 'nosniff')
        self.assertEqual(response.headers['cache-control'], 'no-store')

    def test_cookie_flags_and_clear(self):
        response = self.client.post('/auth/login', headers={'Origin': 'http://testserver'})
        cookie = response.headers.get('set-cookie', '').lower()
        self.assertIn('httponly', cookie)
        self.assertIn('samesite=strict', cookie)
        cleared = self.client.post('/auth/logout', headers={'Origin': 'http://testserver'})
        self.assertIn('max-age=0', cleared.headers.get('set-cookie', '').lower())


    def test_route_coverage_rejects_unprotected_mutations(self):
        app = FastAPI()
        @app.post('/unsafe/write')
        def unsafe_write():
            return {'ok': True}
        with self.assertRaises(UnprotectedRouteError):
            validate_security_routes(app)

    def test_route_coverage_accepts_protected_and_documented_public_routes(self):
        app = FastAPI()
        @app.post('/stations/{station_id}/start')
        @security_gateway_protected
        def start_station():
            return {'ok': True}
        @app.post('/auth/login')
        def login():
            return {'ok': True}
        validate_security_routes(app, public_mutation_routes={'/auth/login': 'Public credential exchange'})

    def test_public_route_requires_rationale(self):
        app = FastAPI()
        @app.post('/auth/login')
        def login():
            return {'ok': True}
        with self.assertRaises(ValueError):
            validate_security_routes(app, public_mutation_routes={'/auth/login': ' '})

    def test_login_rate_limit_is_applied_by_path(self):
        self.client.post('/auth/login', headers={'Origin': 'http://testserver'})
        self.client.post('/auth/login', headers={'Origin': 'http://testserver'})
        limited = self.client.post('/auth/login', headers={'Origin': 'http://testserver'})
        self.assertEqual(limited.status_code, 429)


if __name__ == '__main__':
    unittest.main()
