import os

import aiounittest

os.environ.pop('SEARX_DEBUG', None)
os.environ.pop('SEARX_DEBUG_LOG_LEVEL', None)
os.environ.pop('SEARX_DISABLE_ETC_SETTINGS', None)
os.environ.pop('SEARX_SETTINGS_PATH', None)

os.environ.pop('SEARXNG_SETTINGS_PATH', None)

os.environ['SEARXNG_DEBUG'] = '1'
os.environ['SEARXNG_DEBUG_LOG_LEVEL'] = 'WARNING'
os.environ['SEARXNG_DISABLE_ETC_SETTINGS'] = '1'


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

    def setattr4test(self, obj, attr, value):
        """
        setattr(obj, attr, value)
        but reset to the previous value in the cleanup.
        """
        previous_value = getattr(obj, attr)

        def cleanup_patch():
            setattr(obj, attr, previous_value)

        self.addCleanup(cleanup_patch)
        setattr(obj, attr, value)
