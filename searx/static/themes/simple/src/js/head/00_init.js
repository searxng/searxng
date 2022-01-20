/**
 * @license
 * (C) Copyright Contributors to the SearXNG project.
 * (C) Copyright Contributors to the searx project (2014 - 2021).
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */
/* global DocumentTouch:readonly */
(function (w, d) {
  'use strict';

  // add data- properties
  var script = d.currentScript  || (function () {
    var scripts = d.getElementsByTagName('script');
    return scripts[scripts.length - 1];
  })();

  const enabledPluginIds = JSON.parse(script.getAttribute('data-plugins'));

  // try to detect touch screen
  w.searxng = {
    touch: (("ontouchstart" in w) || w.DocumentTouch && document instanceof DocumentTouch) || false,
    method: script.getAttribute('data-method'),
    autocompleter: script.getAttribute('data-autocompleter') === 'true',
    search_on_category_select: enabledPluginIds['searx.plugins.search_on_category_select'] == true,
    infinite_scroll: enabledPluginIds['searx.plugins.infinite_scroll'] == true,
    hotkeys: enabledPluginIds['searx.plugins.vim_hotkeys'] == true,
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
  if (w.searxng.touch) {
    hmtlElement.classList.add('touch');
  }
})(window, document);
