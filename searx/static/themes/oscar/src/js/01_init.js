/**
 * @license
 * (C) Copyright Contributors to the SearXNG project.
 * (C) Copyright Contributors to the searx project (2014 - 2021).
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

window.searxng = (function(d) {
    'use strict';

    //
    d.getElementsByTagName("html")[0].className = "js";

    // add data- properties
    var script = d.currentScript  || (function() {
        var scripts = d.getElementsByTagName('script');
        return scripts[scripts.length - 1];
    })();

    return {
        autocompleter: script.getAttribute('data-autocompleter') === 'true',
        infinite_scroll: script.getAttribute('data-infinite-scroll') === 'true',
        method: script.getAttribute('data-method'),
        translations: JSON.parse(script.getAttribute('data-translations'))
    };
})(document);
