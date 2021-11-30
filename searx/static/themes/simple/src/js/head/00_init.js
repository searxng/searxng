/**
 * @license
 * (C) Copyright Contributors to the SearXNG project.
 * (C) Copyright Contributors to the searx project (2014 - 2021).
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */
/* global DocumentTouch:readonly */
(function(w, d) {
    'use strict';

    // update the css
    var hmtlElementClassList = d.getElementsByTagName("html")[0].classList;
    hmtlElementClassList.remove('no-js');
    hmtlElementClassList.add('js');

    // try to detect touch screen
    if (("ontouchstart" in w) || w.DocumentTouch && d instanceof DocumentTouch) {
        hmtlElementClassList.add('touch');
    }
})(window, document);