import fasttext
import os
from flask_babel import gettext

name = gettext('Autodetect search language')
description = gettext('Automatically detect the query search language and switch to it.')
preference_section = 'general'
default_on = False


fasttext.FastText.eprint = lambda x: None
model = fasttext.load_model(os.path.dirname(os.path.realpath(__file__)) + '/../data/lid.176.ftz')


def pre_search(request, search):
    lang = model.predict(search.search_query.query, k=1)
    if lang[1][0] >= 0.3:
        search.search_query.lang = lang[0][0].split('__label__')[1]
    return True
