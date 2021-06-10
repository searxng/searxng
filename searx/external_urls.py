import math

from searx.data import EXTERNAL_URLS


IMDB_PREFIX_TO_URL_ID = {
    'tt': 'imdb_title',
    'mn': 'imdb_name',
    'ch': 'imdb_character',
    'co': 'imdb_company',
    'ev': 'imdb_event'
}
HTTP_WIKIMEDIA_IMAGE = 'http://commons.wikimedia.org/wiki/Special:FilePath/'


def get_imdb_url_id(imdb_item_id):
    id_prefix = imdb_item_id[:2]
    return IMDB_PREFIX_TO_URL_ID.get(id_prefix)


def get_wikimedia_image_id(url):
    if url.startswith(HTTP_WIKIMEDIA_IMAGE):
        return url[len(HTTP_WIKIMEDIA_IMAGE):]
    if url.startswith('File:'):
        return url[len('File:'):]
    return url


def get_external_url(url_id, item_id, alternative="default"):
    """Return an external URL or None if url_id is not found.

    url_id can take value from data/external_urls.json
    The "imdb_id" value is automaticaly converted according to the item_id value.

    If item_id is None, the raw URL with the $1 is returned.
    """
    if item_id is not None:
        if url_id == 'imdb_id':
            url_id = get_imdb_url_id(item_id)
        elif url_id == 'wikimedia_image':
            item_id = get_wikimedia_image_id(item_id)

    url_description = EXTERNAL_URLS.get(url_id)
    if url_description:
        url_template = url_description["urls"].get(alternative)
        if url_template is not None:
            if item_id is not None:
                return url_template.replace('$1', item_id)
            else:
                return url_template
    return None


def get_earth_coordinates_url(latitude, longitude, osm_zoom, alternative='default'):
    url = get_external_url('map', None, alternative)\
        .replace('${latitude}', str(latitude))\
        .replace('${longitude}', str(longitude))\
        .replace('${zoom}', str(osm_zoom))
    return url


def area_to_osm_zoom(area):
    """Convert an area in km² into an OSM zoom. Less reliable if the shape is not round.

    logarithm regression using these data:
     * 9596961 -> 4 (China)
     * 3287263 -> 5 (India)
     * 643801 -> 6 (France)
     * 6028 -> 9
     * 1214 -> 10
     * 891 -> 12
     * 12 -> 13

    In WolframAlpha:
        >>> log fit {9596961,15},{3287263, 14},{643801,13},{6028,10},{1214,9},{891,7},{12,6}

    with 15 = 19-4 (China); 14 = 19-5 (India) and so on

    Args:
        area (int,float,str): area in km²

    Returns:
        int: OSM zoom or 19 in area is not a number
    """
    try:
        amount = float(area)
        return max(0, min(19, round(19 - 0.688297 * math.log(226.878 * amount))))
    except ValueError:
        return 19
