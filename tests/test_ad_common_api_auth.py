"""Unit tests for ADCommonAPIAuth.lookup_rfid.

Run from the repository root:  python3 -m unittest discover -s tests -v

The auth driver is exercised off-hardware: requests.get is stubbed, and
the driver's own auth notifications are captured. These are the first
automated tests in the repo; before them the driver carried its author's
note "Untested, and the coder is uninformed."
"""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests  # noqa: E402
from drivers.Auth import ADCommonAPIAuth as auth_module  # noqa: E402


class FakeResponse:
    def __init__(self, status_code=200, payload=None, json_error=False):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self._json_error = json_error

    def json(self):
        if self._json_error:
            raise ValueError("no json")
        return self._payload


class LookupRfidTest(unittest.TestCase):
    def setUp(self):
        config = {"url": "http://commonapi.invalid/badgeGroupMembership",
                  "group": "Infrastructure Interlock Test"}
        self.auth = auth_module.ADCommonAPIAuth(config, loader=None)
        self.verdicts = []
        self.auth.observeAuth(self.verdicts.append)

    def lookup(self, get_result=None, get_side_effect=None):
        with mock.patch.object(auth_module.requests, "get") as get:
            if get_side_effect is not None:
                get.side_effect = get_side_effect
            else:
                get.return_value = get_result
            self.auth.lookup_rfid("0012345678")
            return get

    def test_granted_when_in_group_and_active(self):
        self.lookup(FakeResponse(payload={"inGroup": True, "activeMember": True}))
        self.assertEqual(self.verdicts,
                         [{"authorized": True, "id": "0012345678"}])

    def test_denied_when_not_in_group(self):
        self.lookup(FakeResponse(payload={"inGroup": False, "activeMember": True}))
        self.assertEqual(self.verdicts[0]["authorized"], False)

    def test_denied_when_in_group_but_not_active_member(self):
        # The pre-fix code authorized this badge: it only read inGroup.
        self.lookup(FakeResponse(payload={"inGroup": True, "activeMember": False}))
        self.assertEqual(self.verdicts[0]["authorized"], False)

    def test_missing_keys_deny_instead_of_keyerror(self):
        self.lookup(FakeResponse(payload={}))
        self.assertEqual(self.verdicts[0]["authorized"], False)

    def test_http_error_denies(self):
        self.lookup(FakeResponse(status_code=500))
        self.assertEqual(self.verdicts[0]["authorized"], False)

    def test_unparseable_json_denies(self):
        self.lookup(FakeResponse(json_error=True))
        self.assertEqual(self.verdicts[0]["authorized"], False)

    def test_connection_error_denies_instead_of_crashing(self):
        # Pre-fix this propagated out of the Observer notification and
        # the RFID reader exited the whole application (os._exit(42)).
        self.lookup(get_side_effect=requests.ConnectionError("unreachable"))
        self.assertEqual(self.verdicts[0]["authorized"], False)

    def test_timeout_error_denies_instead_of_hanging(self):
        self.lookup(get_side_effect=requests.ConnectTimeout("slow"))
        self.assertEqual(self.verdicts[0]["authorized"], False)

    def test_request_carries_a_timeout(self):
        get = self.lookup(FakeResponse(payload={"inGroup": True,
                                                "activeMember": True}))
        _, kwargs = get.call_args
        self.assertIn("timeout", kwargs)


if __name__ == "__main__":
    unittest.main()
