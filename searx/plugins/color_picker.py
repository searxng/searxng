from flask_babel import gettext as _
from searx.plugins import Plugin, PluginInfo
from searx.result_types import EngineResults


class SXNGPlugin(Plugin):

    id = "color_picker"

    keywords = ["color picker", "color wheel", "color", "colorpicker", "rgb picker"]

    def __init__(self, plg_cfg):
        super().__init__(plg_cfg)
        self.info = PluginInfo(
            id=self.id, name=_("Hello"), description=_("demo plugin")
        )

    def post_search(self, request, search):
        results = EngineResults()
        if search.search_query.query in self.keywords:
            results.add(results.types.ColorPicker())
        return results
