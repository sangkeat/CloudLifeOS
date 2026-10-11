import hashlib
import http.client
import json
import tempfile
import threading
import unittest
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from cloudlifeos import server


class HealthTests(unittest.TestCase):
    def test_refresh_and_source_changes_require_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            manifest = {'repository':'sangkeat/LifeOS-Foundry','branch':'main','revision':'a'*40,
                        'observed_at':datetime.now(timezone.utc).isoformat(), 'files':{}}
            (directory/'source.json').write_text(json.dumps(manifest))
            with patch.object(server,'LOCAL',directory):
                healthy = server.health(manifest)
                self.assertFalse(healthy['source_changed_since_start'])
                self.assertTrue(healthy['channels'][1]['ready_for_scope'])
                self.assertIsNone(healthy['channels'][1]['effective']['authenticated'])
                for record in healthy['channels'][2:]:
                    self.assertFalse(record['ready_for_scope'])
                updated = {**manifest,'observed_at':'2026-10-12T12:00:00+00:00'}
                (directory/'source.json').write_text(json.dumps(updated))
                result = server.health(manifest)
                self.assertTrue(result['source_changed_since_start'])
                self.assertFalse(result['channels'][1]['ready_for_scope'])

    def test_changed_or_missing_source_bytes_never_claim_current(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory/'sample.py').write_bytes(b'original')
            manifest = {'repository':'source','branch':'main','revision':'a'*40,
                        'observed_at':datetime.now(timezone.utc).isoformat(),
                        'files':{'sample.py':hashlib.sha256(b'original').hexdigest()}}
            (directory/'source.json').write_text(json.dumps(manifest))
            with patch.object(server,'LOCAL',directory),patch.object(server,'CORE',directory):
                self.assertTrue(server.health(manifest)['channels'][1]['ready_for_scope'])
                (directory/'sample.py').write_bytes(b'tampered')
                self.assertFalse(server.health(manifest)['channels'][1]['ready_for_scope'])
                (directory/'sample.py').unlink()
                self.assertFalse(server.health(manifest)['channels'][1]['ready_for_scope'])


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest, monitor = server.load_source()
        cls.directory = tempfile.TemporaryDirectory()
        cls.local = Path(cls.directory.name)
        (cls.local/'snapshots').mkdir()
        (cls.local/'status').mkdir()
        (cls.local/'source.json').write_text(json.dumps(manifest))
        for path in (server.LOCAL/'snapshots').glob('*.json'):
            (cls.local/'snapshots'/path.name).write_bytes(path.read_bytes())
            (cls.local/'status'/path.name).write_bytes(path.read_bytes())
        cls.local_patch = patch.object(server, 'LOCAL', cls.local)
        cls.local_patch.start()
        cls.http = ThreadingHTTPServer(('127.0.0.1',0),server.make_handler(manifest,monitor))
        cls.port = cls.http.server_port
        cls.thread = threading.Thread(target=cls.http.serve_forever,daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown(); cls.http.server_close(); cls.thread.join()
        cls.local_patch.stop(); cls.directory.cleanup()

    def request(self,path='/',method='GET',headers=None):
        conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5)
        conn.request(method,path,headers=headers or {})
        response=conn.getresponse(); body=response.read(); status=response.status
        headers=dict(response.getheaders());conn.close()
        return status,headers,body

    def test_functional_read_and_upstream_monitor(self):
        status,headers,body=self.request('/api/health')
        self.assertEqual(status,200)
        payload=json.loads(body)
        self.assertEqual(payload['source']['repository'],'sangkeat/LifeOS-Foundry')
        self.assertTrue(payload['channels'][0]['ready_for_scope'])
        self.assertEqual(headers['Cache-Control'],'no-store')
        self.assertEqual(self.request('/monitor')[0],200)
        legacy=json.loads(self.request('/api/status')[2])
        self.assertEqual(legacy['projection']['mode'],'snapshot')
        self.assertTrue(all(c['state']=='unknown' and not c['is_live'] for c in legacy['connections'].values()))

    def test_host_rebinding_and_cross_origin_denied(self):
        self.assertEqual(self.request('/api/health',headers={'Host':'attacker.example'})[0],403)
        self.assertEqual(self.request('/api/status',headers={'Origin':'https://attacker.example'})[0],403)

    def test_no_write_api_or_arbitrary_file_access(self):
        for method in ['POST','PUT','DELETE','PATCH']:
            self.assertEqual(self.request('/api/status',method)[0],405)
        for path in ['/.git/config','/.local/source.json','/../scripts/bootstrap.py','/%2e%2e/.git/config','/api/runtime']:
            self.assertEqual(self.request(path)[0],404)

    def test_source_dates_are_record_dates_not_request_time(self):
        result=json.loads(self.request('/api/source-summary')[2])
        snapshot=json.loads((server.LOCAL/'snapshots/goal-registry.json').read_text())
        self.assertEqual(result['goal-registry']['record_updated_at'],snapshot['updated_at'])
        self.assertEqual(result['goal-registry']['mode'],'snapshot')

    def test_source_drift_blocks_executable_assets_and_projection_routes(self):
        path=self.local/'source.json'; original=path.read_bytes()
        try:
            altered=json.loads(original);altered['revision']='b'*40
            path.write_text(json.dumps(altered))
            for route in ['/monitor','/owner-status.js','/api/status','/api/source-summary']:
                self.assertEqual(self.request(route)[0],503)
            self.assertTrue(json.loads(self.request('/api/health')[2])['source_changed_since_start'])
        finally:
            path.write_bytes(original)

    def test_mixed_snapshot_and_derived_snapshot_fail_closed(self):
        for folder, route in [('snapshots','/api/source-summary'),('status','/api/status')]:
            path=self.local/folder/'goal-registry.json';original=path.read_bytes()
            try:
                path.write_text('{"updated_at":"2099-01-01"}')
                self.assertEqual(self.request(route)[0],503)
            finally:
                path.write_bytes(original)


if __name__ == '__main__':
    unittest.main()
