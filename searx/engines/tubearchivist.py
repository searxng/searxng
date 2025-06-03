# SPDX-License-Identifier: AGPL-3.0-or-later
"""`Tube Archivist`_ - *Your self hosted YouTube media server.*

.. _Tube Archivist: https://www.tubearchivist.com

This engine connects with a self-hosted instance of `Tube Archivist`_ to allow
searching for your hosted videos.

`Tube Archivist`_ (TA) requires authentication for all image loads via cookie
authentication.  What this means is that by default, SearXNG will have no way to
pull images from TA (as there is no way to pass cookies in a URL string only).

In the meantime while work is done on the TA side, this can be worked around by
bypassing auth for images in TA by altering the default TA nginx file.

This is located in the main tubearchivist docker container at::

  /etc/nginx/sites-available/default

It is **strongly** recommended first setting up the intial connection and
verying searching works first with broken images, and then attempting this
change.  This will limit any debugging to only images, rather than
tokens/networking.

Steps to enable **unauthenticated** metadata access for channels and videos:

#. Perform any backups of TA before editing core configurations.

#. Copy the contents of the file ``/etc/nginx/sites-available/default`` in the
   TA docker container

#. Edit ``location /cache/videos`` and ``location /cache/channels``.  Comment
   out the line ``auth_request /api/ping/;`` to ``# auth_request /api/ping/;``.

#. Save the file to wherever you normally store your docker configuration.

#. Mount this new configuration over the default configuration.  With ``docker
   run``, this would be::

     -v ./your-new-config.yml:/etc/nginx/sites-available/default

   With ``docker compose``, this would be::

     - "./your-new-config.yml:/etc/nginx/sites-available/default:ro"

#. Start the TA container.

After these steps, double check that TA works as normal (nothing should be
different on the TA side).  Searching again should now show images.


Configuration
=============

The engine has the following required settings:

- :py:obj:`base_url`
- :py:obj:`ta_token`

Optional settings:

- :py:obj:`ta_link_to_mp4`

.. code:: yaml

  - name: tubearchivist
    engine: tubearchivist
    shortcut: tuba
    base_url:
    ta_token:
    ta_link_to_mp4: true

Implementations
===============
"""

from __future__ import annotations

from urllib.parse import urlencode
from dateutil.parser import parse
from searx.utils import html_to_text, humanize_number
from searx.result_types import EngineResults

about = {
    # pylint: disable=line-too-long
    "website": 'https://www.tubearchivist.com',
    "official_api_documentation": 'https://docs.tubearchivist.com/api/introduction/',
    "use_official_api": True,
    "require_api_key": False,
    "results": 'JSON',
}

# engine dependent config
categories = ["videos"]
paging = True

base_url = ""
"""Base URL of the Tube Archivist instance.  Fill this in with your own
Tube Archivist URL (``http://your-instance:port``)."""

ta_token: str = ""
"""The API key to use for Authorization_ header.  Can be found under:

  :menuselection:`Settings --> User --> Admin Interface`.

.. _Authorization: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Authorization
"""

ta_link_to_mp4: bool = False
"""Optional, if true SearXNG will link directly to the mp4 of the video to play
in the browser.  The default behavior is to link into TubeArchivist's interface
directly."""


def absolute_url(relative_url):
    return f'{base_url.rstrip("/")}{relative_url}'


def init(_):
    if not base_url:
        raise ValueError('tubearchivist engine: base_url is unset')
    if not ta_token:
        raise ValueError('tubearchivist engine: ta_token is unset')


def request(query, params):
    if not query:
        return False

    args = {'query': query}
    params['url'] = f"{base_url.rstrip('/')}/api/search?{urlencode(args)}"
    params['headers']['Authorization'] = f'Token {ta_token}'

    return params


def response(resp) -> EngineResults:
    results = EngineResults()
    video_response(resp, results)
    return results


def video_response(resp, results: EngineResults) -> None:
    """Parse video response from Tubearchivist instances."""

    json_data = resp.json()

    if 'results' not in json_data:
        return

    for channel_result in json_data['results']['channel_results']:
        channel_url = absolute_url(f'/channel/{channel_result["channel_id"]}')

        res = results.types.MainResult(
            url=channel_url,
            title=channel_result['channel_name'],
            content=html_to_text(channel_result['channel_description']),
            author=channel_result['channel_name'],
            views=humanize_number(channel_result['channel_subs']),
            thumbnail=f'{absolute_url(channel_result["channel_thumb_url"])}?auth={ta_token}',
        )

        results.add(result=res)

    for video_result in json_data['results']['video_results']:
        metadata = list(filter(None, [video_result['channel']['channel_name'], *video_result.get('tags', [])]))[:5]
        if ta_link_to_mp4:
            url = f'{base_url.rstrip("/")}{video_result["media_url"]}'
        else:
            url = f'{base_url.rstrip("/")}/?videoId={video_result["youtube_id"]}'

        # a type for the video.html template is not yet implemented
        # --> using LegacyResult

        kwargs = {
            'template': 'videos.html',
            'url': url,
            'title': video_result['title'],
            'content': html_to_text(video_result['description']),
            'author': video_result['channel']['channel_name'],
            'length': video_result['player']['duration_str'],
            'views': humanize_number(video_result['stats']['view_count']),
            'publishedDate': parse(video_result['published']),
            'thumbnail': f'{absolute_url(video_result["vid_thumb_url"])}?auth={ta_token}',
            'metadata': ' | '.join(metadata),
        }
        results.add(results.types.LegacyResult(**kwargs))
