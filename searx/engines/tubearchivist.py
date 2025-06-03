# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tube Archivist - Your self hosted YouTube media server.  Connects with a self-hosted instance of
Tube Archivist to allow searching for your hosted videos.

Configuration
=============

The engine has the following (required) settings:


``base_url``:
  TubeArchivist endpoint URL. (http://your-instance:port)

``token``:
  The API key to use for authentication.
  (Can be found under Settings -> User -> Admin Interface)

``link_to_mp4``:
  Optional, defaults to False.
  When true, will link directly into the mp4 of the hosted video rather than into TubeArchivist's interface.

Notes
=====

TubeArchivist requires authentication for all image loads via cookie authentication.  What this means is that by
default, SearXNG will have no way to pull images from TubeArchivist (as there is no way to pass cookies in a URL
string only).

In the meantime while work is done on the TubeArchivist side, this can be worked around by bypassing auth for
images in TubeArchivist by altering the default TubeArchivist nginx file.

This is located in the main tubearchivist docker container at `/etc/nginx/sites-available/default`.

It is **strongly** recommended first setting up the intial connection and verying searching works first with
broken images, and then attempting this change.  This will limit any debugging to only images, rather than
tokens/networking.

Steps to enable **unauthenticated** metadata access for channels and videos:

  1. Perform any backups of TubeArchivist before editing core configurations.
  2.  Copy the contents of the file `/etc/nginx/sites-available/default` in the TA docker container
  3. Edit `location /cache/videos` and `location /cache/channels`

    - Comment out the line `auth_request /api/ping/;` to `# auth_request /api/ping/;`.

  4. Save the file to wherever you normally store your docker configuration.
  5. Mount this new configuration over the default configuration.

    - With docker run, this would be `-v ./your-new-config.yml:/etc/nginx/sites-available/default`
    - With docker compose, this would be
        `- "./your-new-config.yml:/etc/nginx/sites-available/default:ro"`

  6. Start the TA container.

After these steps, double check that TA works as normal (nothing should be different on the TA side).
Searching again should now show images.

"""

from urllib.parse import urlencode
from dateutil.parser import parse
from searx.utils import html_to_text, humanize_number

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
"""Base URL of the Tube Archivist instance.  Fill this in with your own tubearchivist url
"""


token = ""
"""The API key to use for authentication.
"""

link_to_mp4 = False
"""Optional, if true SearXNG will link directly to the mp4 of the video to play in the browser.
The default behavior is to link into TubeArchivist's interface directly.
"""


def request(query, params):
    """Assemble request for the Tubearchivist API"""

    if not query:
        return False

    args = {
        'query': query,
    }
    params['url'] = f"{base_url.rstrip('/')}/api/search?{urlencode(args)}"
    params['headers']['Authorization'] = f'Token {token}'

    return params


def response(resp):
    return video_response(resp)


def video_response(resp):
    """Parse video response from Tubearchivist instances."""
    results = []

    json_data = resp.json()

    if 'results' not in json_data:
        return []

    for channel_result in json_data['results']['channel_results']:
        channel_url = absolute_url(f'/channel/{channel_result["channel_id"]}')
        results.append(
            {
                'url': channel_url,
                'title': channel_result['channel_name'],
                'content': html_to_text(channel_result['channel_description']),
                'author': channel_result['channel_name'],
                'views': humanize_number(channel_result['channel_subs']),
                'thumbnail': f'{absolute_url(channel_result["channel_thumb_url"])}?auth={token}',
            }
        )

    for video_result in json_data['results']['video_results']:
        metadata = list(filter(None, [video_result['channel']['channel_name'], *video_result.get('tags', [])]))[:5]
        if link_to_mp4:
            url = f'{base_url.rstrip("/")}{video_result["media_url"]}'
        else:
            url = f'{base_url.rstrip("/")}/?videoId={video_result["youtube_id"]}'
        results.append(
            {
                'template': 'videos.html',
                'url': url,
                'title': video_result['title'],
                'content': html_to_text(video_result['description']),
                'author': video_result['channel']['channel_name'],
                'length': video_result['player']['duration_str'],
                'views': humanize_number(video_result['stats']['view_count']),
                'publishedDate': parse(video_result['published']),
                'thumbnail': f'{absolute_url(video_result["vid_thumb_url"])}?auth={token}',
                'metadata': ' | '.join(metadata),
            }
        )

    return results


def absolute_url(relative_url):
    return f'{base_url.rstrip("/")}{relative_url}'
