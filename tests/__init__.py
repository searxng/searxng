# SPDX-License-Identifier: AGPL-3.0-or-later
# pylint: disable=missing-module-docstring,disable=missing-class-docstring,invalid-name

import os
import pathlib
from contextlib import contextmanager

import aiounittest

os.environ.pop('SEARXNG_SETTINGS_PATH', None)
os.environ['SEARXNG_DISABLE_ETC_SETTINGS'] = '1'


@contextmanager
def _scoped_request(app, path: str, method: str = "GET", **kwargs):
    # pylint: disable=import-outside-toplevel
    from searx.extended_types import SXNG_Request, reset_request, set_request

    with app.test_request_context(path, method=method, **kwargs) as ctx:
        req = SXNG_Request.from_flask_request(ctx.request)
        token = set_request(req)
        try:
            yield
        finally:
            reset_request(token)


class SearxTestLayer:
    """Base layer for non-robot tests."""

    __name__ = 'SearxTestLayer'

    @classmethod
    def setUp(cls):
        pass

    @classmethod
    def tearDown(cls):
        pass

    @classmethod
    def testSetUp(cls):
        pass

    @classmethod
    def testTearDown(cls):
        pass


class SearxTestCase(aiounittest.AsyncTestCase):
    """Base test case for non-robot tests."""

    layer = SearxTestLayer

    SETTINGS_FOLDER = pathlib.Path(__file__).parent / "unit" / "settings"
    TEST_SETTINGS = "test_settings.yml"

    def scoped_request(self, path: str = "/search"):
        """Enter both a Flask request context and the kernel request scope."""
        return _scoped_request(self.app, path)

    def setUp(self):
        self.init_test_settings()

    def setattr4test(self, obj, attr, value):
        """setattr(obj, attr, value) but reset to the previous value in the
        cleanup."""
        previous_value = getattr(obj, attr)

        def cleanup_patch():
            setattr(obj, attr, previous_value)

        self.addCleanup(cleanup_patch)
        setattr(obj, attr, value)

    def init_test_settings(self):
        """Sets ``SEARXNG_SETTINGS_PATH`` environment variable an initialize
        global ``settings`` variable and the ``logger`` from a test config in
        :origin:`tests/unit/settings/`.
        """

        os.environ['SEARXNG_SETTINGS_PATH'] = str(self.SETTINGS_FOLDER / self.TEST_SETTINGS)

        # pylint: disable=import-outside-toplevel
        import searx
        import searx.locales
        import searx.plugins
        import searx.search
        import searx.webapp

        # https://flask.palletsprojects.com/en/stable/config/#builtin-configuration-values
        # searx.webapp.app.config["DEBUG"] = True
        searx.webapp.app.config["TESTING"] = True  # to get better error messages
        searx.webapp.app.config["EXPLAIN_TEMPLATE_LOADING"] = True

        searx.init_settings()
        searx.plugins.initialize(searx.webapp.app)

        # searx.search.initialize will:
        # - load the engines and
        # - initialize searx.network, searx.metrics, searx.processors and searx.search.checker

        searx.search.initialize(
            check_network=True,
            enable_metrics=searx.get_setting("general.enable_metrics"),
        )

        # pylint: disable=attribute-defined-outside-init
        self.app = searx.webapp.app
        self.client = self.app.test_client()
