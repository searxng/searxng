/**
 * @license
 * (C) Copyright Contributors to the SearXNG project.
 * (C) Copyright Contributors to the searx project (2014 - 2021).
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */
(function (w, d) {
  'use strict';

  // add data- properties
  var script = d.currentScript  || (function () {
    var scripts = d.getElementsByTagName('script');
    return scripts[scripts.length - 1];
  })();

  // try to detect touch screen
  w.searxng = {
    method: script.getAttribute('data-method'),
    autocompleter: script.getAttribute('data-autocompleter') === 'true',
    search_on_category_select: script.getAttribute('data-search-on-category-select') === 'true',
    infinite_scroll: script.getAttribute('data-infinite-scroll') === 'true',
    hotkeys: script.getAttribute('data-hotkeys') === 'true',
    static_path: script.getAttribute('data-static-path'),
    translations: JSON.parse(script.getAttribute('data-translations')),
    theme: {
      // image that is displayed if load of <img src='...'> failed
      img_load_error: 'img/img_load_error.svg'
    }
  };

  // update the css
  var hmtlElement = d.getElementsByTagName("html")[0];
  hmtlElement.classList.remove('no-js');
  hmtlElement.classList.add('js');
})(window, document);