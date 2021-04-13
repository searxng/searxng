# SPDX-License-Identifier: AGPL-3.0-or-later

from searx import logger
from searx.search.processors.abstract import EngineProcessor


logger = logger.getChild('searx.search.processor.offline')


class OfflineProcessor(EngineProcessor):

    engine_type = 'offline'

    def _search_basic(self, query, params):
        return self.engine.search(query, params)

    def search(self, query, params, result_container, start_time, timeout_limit):
        try:
            search_results = self._search_basic(query, params)
            self.extend_container(result_container, start_time, search_results)
        except ValueError as e:
            # do not record the error
            logger.exception('engine {0} : invalid input : {1}'.format(self.engine_name, e))
        except Exception as e:
            self.handle_exception(result_container, 'unexpected crash', e)
            logger.exception('engine {0} : exception : {1}'.format(self.engine_name, e))
