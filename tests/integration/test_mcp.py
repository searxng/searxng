"""MCP plugin integration tests. Run: .venv/bin/python -m unittest tests.integration.test_mcp"""

import subprocess
import time
import signal
import requests
from tests import SearxTestCase


class TestMCPIntegration(SearxTestCase):
    @classmethod
    def setUpClass(cls):
        cls.proc = subprocess.Popen(
            [".venv/bin/python", "-m", "searx"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(3)

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.wait()

    def test_get_engines_via_http(self):
        resp = requests.post(
            "http://127.0.0.1:8765/mcp",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "get_engines", "arguments": {}},
                "id": 1,
            },
            timeout=60,
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.text
        self.assertIn("general", data)
        self.assertNotIn("dictionaries", data)

    def test_search_via_http(self):
        resp = requests.post(
            "http://127.0.0.1:8765/mcp",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "search", "arguments": {"query": "test"}},
                "id": 2,
            },
            timeout=60,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("title", resp.text)
