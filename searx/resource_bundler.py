"""
Bundles ``js_dependencies`` of plugins to remove the overhead of separate HTTP requests.
"""
import os
import os.path
import itertools
import pathlib
from typing import Iterable, Dict

from flask import url_for

from . import settings
from .webutils import get_themes
from .plugins import plugins, Plugin

templates_path = settings['ui']['templates_path']
themes = get_themes(templates_path)


def build_bundles():
    static_path = settings['ui']['static_path']
    bundles_path = pathlib.Path(static_path).joinpath('bundles')
    bundles_path.mkdir(exist_ok=True)

    # delete all bundles
    for js_file in bundles_path.glob('*.js'):
        js_file.unlink()

    # generate bundles
    for theme in themes:
        modules: Dict[str, str] = {}

        for plugin in plugins:
            js_deps = [dep.path for dep in plugin.js_dependencies if theme in dep.themes]
            if js_deps:
                js = ''
                for path in js_deps:
                    with open(os.path.join(static_path, path), encoding='utf-8') as s:
                        # We wrap the code in a self-calling function to prevent
                        # namespace collisions between scripts.
                        js += f'/** {path} **/\n(function(){{\n{s.read()}\n}})();'

                modules[plugin.id] = js

        for i in range(1, len(modules) + 1):
            for plugin_combination in itertools.combinations(modules, i):
                with bundles_path.joinpath(_bundle_path(theme, plugin_combination)).open('w', encoding='utf-8') as f:
                    js = ''
                    for plugin in plugin_combination:
                        js += f'/**** {plugin} ****/\n' + modules[plugin]
                    f.write(js)


def get_bundle_url(theme: str, plugins: Iterable[Plugin]):
    plugin_ids = [p.id for p in plugins if any(dep for dep in p.js_dependencies if theme in dep.themes)]
    if plugin_ids:
        return url_for('static', filename='bundles/' + _bundle_path(theme, sorted(plugin_ids)))
    else:
        return None


def _bundle_path(theme: str, sorted_plugin_ids: Iterable[str]):
    return theme + '+' + '+'.join(sorted_plugin_ids) + '.js'
