# SPDX-License-Identifier: AGPL-3.0-or-later
# lint: pylint
"""Plugin to detect the search language from the search query.

The language detection is done by using the fastText_ library (`python
fasttext`_). fastText_ distributes the `language identification model`_, for
reference:

- `FastText.zip: Compressing text classification models`_
- `Bag of Tricks for Efficient Text Classification`_

The `language identification model`_ support the language codes (ISO-639-3)::

   af als am an ar arz as ast av az azb ba bar bcl be bg bh bn bo bpy br bs bxr
   ca cbk ce ceb ckb co cs cv cy da de diq dsb dty dv el eml en eo es et eu fa
   fi fr frr fy ga gd gl gn gom gu gv he hi hif hr hsb ht hu hy ia id ie ilo io
   is it ja jbo jv ka kk km kn ko krc ku kv kw ky la lb lez li lmo lo lrc lt lv
   mai mg mhr min mk ml mn mr mrj ms mt mwl my myv mzn nah nap nds ne new nl nn
   no oc or os pa pam pfl pl pms pnb ps pt qu rm ro ru rue sa sah sc scn sco sd
   sh si sk sl so sq sr su sv sw ta te tg th tk tl tr tt tyv ug uk ur uz vec vep
   vi vls vo wa war wuu xal xmf yi yo yue zh

The `language identification model`_ is harmonized with the SearXNG's language
(locale) model.  General conditions of SearXNG's locale model are:

a. SearXNG's locale of a query is passed to the
   :py:obj:`searx.locales.get_engine_locale` to get a language and/or region
   code that is used by an engine.

b. SearXNG and most of the engines do not support all the languages from
   language model and there might be also a discrepancy in the ISO-639-3 and
   ISO-639-2 handling (:py:obj:`searx.locales.get_engine_locale`).  Further
   more, in SearXNG the locales like ``zh-TH`` (``zh-CN``) are mapped to
   ``zh_Hant`` (``zh_Hans``).

Conclusion: This plugin does only auto-detect the languages a user can select in
the language menu (:py:obj:`supported_langs`).

SearXNG's locale of a query comes from (*highest wins*):

1. The ``Accept-Language`` header from user's HTTP client.
2. The user select a locale in the preferences.
3. The user select a locale from the menu in the query form (e.g. ``:zh-TW``)
4. This plugin is activated in the preferences and the locale (only the language
   code / none region code) comes from the fastText's language detection.

Conclusion: There is a conflict between the language selected by the user and
the language from language detection of this plugin.  For example, the user
explicitly selects the German locale via the search syntax to search for a term
that is identified as an English term (try ``:de-DE thermomix``, for example).

.. hint::

   To SearXNG maintainers; please take into account: under some circumstances
   the auto-detection of the language of this plugin could be detrimental to
   users expectations.  Its not recommended to activate this plugin by
   default. It should always be the user's decision whether to activate this
   plugin or not.

.. _fastText: https://fasttext.cc/
.. _python fasttext: https://pypi.org/project/fasttext/
.. _language identification model: https://fasttext.cc/docs/en/language-identification.html
.. _Bag of Tricks for Efficient Text Classification: https://arxiv.org/abs/1607.01759
.. _`FastText.zip: Compressing text classification models`: https://arxiv.org/abs/1612.03651

"""

from flask_babel import gettext
import babel

from searx.utils import detect_language
from searx.languages import language_codes

name = gettext('Autodetect search language')
description = gettext('Automatically detect the query search language and switch to it.')
preference_section = 'general'
default_on = False

supported_langs = set()
"""Languages supported by most searxng engines (:py:obj:`searx.languages.language_codes`)."""


def pre_search(request, search):  # pylint: disable=unused-argument
    lang = detect_language(search.search_query.query, min_probability=0)
    if lang in supported_langs:
        search.search_query.lang = lang
        try:
            search.search_query.locale = babel.Locale.parse(lang)
        except babel.core.UnknownLocaleError:
            pass
    return True


def init(app, settings):  # pylint: disable=unused-argument
    for searxng_locale in language_codes:
        supported_langs.add(searxng_locale[0].split('-')[0])
    return True
