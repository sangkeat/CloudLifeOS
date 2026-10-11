import unittest
from datetime import datetime, timedelta, timezone
from cloudlifeos.evidence import project

NOW = datetime(2026, 10, 11, 12, 0, tzinfo=timezone.utc)


class EvidenceTests(unittest.TestCase):
    def record(self, **kwargs):
        return dict(mode='live', observed_at=NOW.isoformat(), ttl_seconds=300,
                    connected=True, authenticated=None, admitted=True, verified_working=True, **kwargs)

    def test_successful_read_does_not_invent_authentication(self):
        result = project(self.record(), NOW)
        self.assertTrue(result['ready_for_scope'])
        self.assertIsNone(result['effective']['authenticated'])

    def test_expiry_demotes_every_flag(self):
        result = project(self.record(), NOW + timedelta(seconds=301))
        self.assertEqual(result['freshness'], 'stale')
        self.assertFalse(result['ready_for_scope'])
        self.assertTrue(all(v is None for v in result['effective'].values()))
        self.assertTrue(result['verified_working'])  # retain historical observation

    def test_offline_snapshot_cannot_be_runtime_ready_even_if_recent(self):
        record = self.record(); record['mode'] = 'snapshot'
        self.assertFalse(project(record, NOW)['ready_for_scope'])
        self.assertTrue(all(v is None for v in project(record, NOW)['effective'].values()))

    def test_missing_naive_invalid_and_future_times_fail_closed(self):
        for value in [None, '', 'bad', '2026-10-11T12:00:00', (NOW + timedelta(minutes=10)).isoformat()]:
            with self.subTest(value=value):
                record = self.record(); record['observed_at'] = value
                self.assertFalse(project(record, NOW)['ready_for_scope'])

    def test_invalid_ttl_and_non_boolean_claims_fail_closed(self):
        for value in [None, 0, -1, '300', True, 100000]:
            record = self.record(); record['ttl_seconds'] = value
            self.assertFalse(project(record, NOW)['ready_for_scope'])
        record = self.record(); record['verified_working'] = 'true'
        self.assertFalse(project(record, NOW)['ready_for_scope'])

    def test_admission_does_not_imply_success(self):
        record = self.record(); record['verified_working'] = False
        self.assertFalse(project(record, NOW)['ready_for_scope'])


if __name__ == '__main__':
    unittest.main()
