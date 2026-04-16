"""MCP plugin tests. Run: .venv/bin/python -m unittest tests.unit.test_plugin_mcp"""

from tests import SearxTestCase


class TestMCPPlugin(SearxTestCase):
    def test_plugin_info(self):
        from searx.plugins.mcp import MCPPlugin
        from searx.plugins._core import PluginCfg

        plugin = MCPPlugin(PluginCfg())

        self.assertEqual(plugin.id, "mcp")
        self.assertEqual(plugin.info.id, "mcp")
        self.assertEqual(plugin.info.name, "MCP Service")

    def test_get_engines(self):
        from searx.plugins.mcp import get_engines

        result = get_engines()

        self.assertIsInstance(result, dict)
        self.assertIn("general", result)
        self.assertNotIn("dictionaries", result)
        self.assertIsInstance(result["general"], list)

    def test_search_empty_query(self):
        from searx.plugins.mcp import search

        result = search("")

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIn("error", result[0])

    def test_search_invalid_engines(self):
        from searx.plugins.mcp import search

        result = search("test", engines="nonexistent")

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIn("error", result[0])
