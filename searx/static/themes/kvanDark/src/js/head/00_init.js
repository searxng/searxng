/* SPDX-License-Identifier: AGPL-3.0-or-later */
(function (w, d) {
  'use strict';

  // add data- properties
  var script = d.currentScript  || (function () {
    var scripts = d.getElementsByTagName('script');
    return scripts[scripts.length - 1];
  })();

  w.searxng = {
    settings: JSON.parse(atob(script.getAttribute('client_settings')))
  };

  // update the css
  var hmtlElement = d.getElementsByTagName("html")[0];
  hmtlElement.classList.remove('no-js');
  hmtlElement.classList.add('js');

})(window, document);
