"""
The **URL Rewrite plugin** allows modification of search result URLs based on regular expression patterns.
URLs can be rewritten to different destinations, blocked entirely, or have their priority adjusted in the
results list.

The plugin can be enabled by adding it to the `enabled_plugins` **list** in the `settings.yml`:

.. code:: yaml

    enabled_plugins:
        - 'URL Rewrite'
        ...

Configuration options in `settings.yml`:

- ``url_rewrite.rules``: A **list** of rules that define how URLs should be handled. Each rule
  can contain the following keys:

  - ``pattern``: Regular expression pattern to match against result URLs
  - ``repl``: Replacement string for matched URLs, or `false` to remove matching results
  - ``priority``: Optional priority adjustment ('high' or 'low') for matching results

Example configuration:

.. code:: yaml

    url_rewrite:
        rules:
            - pattern: '^(?P<url>https://(.*\.)?cnn\.com/.*)$'
              repl: 'https://reader.example.com/?url=\g<url>'
            - pattern: '^https?://(?:www\.)?facebook\.com/.*'
              repl: false
            - pattern: '^(?P<url>https://news\.example\.com/.*)$'
              repl: 'https://proxy.example.com/?url=\g<url>'
              priority: high

In this example:
- CNN articles are redirected through a reader service
- Facebook URLs are removed from results
- News site URLs are proxied and given higher priority

The ``pattern`` field supports Python regular expressions with named capture groups.
The ``repl`` field can reference captured groups using ``\g<name>`` syntax.
Setting ``repl`` to ``false`` will remove matching results entirely.
The optional ``priority`` field can be set to 'high' or 'low' to adjust result ranking.
"""
import re
from urllib.parse import urlparse

from flask_babel import gettext

from searx import settings
from searx.settings_loader import get_yaml_cfg
from searx.plugins import logger


name = gettext("URL Rewrite")
description = gettext("Rewrite URLs of search results")
default_on = True
preference_section = 'general'
plugin_id = 'url_rewrite'


logger = logger.getChild(plugin_id)
config = settings.get(plugin_id, {})
rules = config.get("rules", [])


def on_result(request, search, result):
    if not rules:
        logger.debug("No url rewrite rules found in settings")
        return True

    if 'url' not in result:
        logger.debug("No url found in result")
        return True

    for rewrite in rules:
        pattern = rewrite.get('pattern')
        repl = rewrite.get('repl')
        priority = rewrite.get('priority')
        replace_url = rewrite.get('replace_url', True)
        
        if not pattern:
            continue

        if repl is None:
            logger.debug(f'No repl found for pattern {pattern}, skipping')
            continue

        if re.search(pattern, result['url']):
            if repl is False:
                logger.info(f'Dropping {result["url"]} - matched {pattern}')
                return False
            
            new_url = re.sub(pattern, repl, result['url'])
            result['url'] = new_url
            
            if replace_url:
                result['parsed_url'] = urlparse(new_url)
            
            if priority:
                result['priority'] = priority
                logger.info(f'Set priority to {priority} for {result["url"]}')

            logger.info(f'Rewrote {result["url"]} using pattern {pattern}')
            break

    return True
