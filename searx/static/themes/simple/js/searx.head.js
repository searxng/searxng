/**
* searx is free software: you can redistribute it and/or modify
* it under the terms of the GNU Affero General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
*
* searx is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU Affero General Public License for more details.
*
* You should have received a copy of the GNU Affero General Public License
* along with searx. If not, see < http://www.gnu.org/licenses/ >.
*
* (C) 2019 by Alexandre Flament
*
*/
/* global DocumentTouch:readonly */
(function(w, d) {
    'use strict';

    // add data- properties
    var script = d.currentScript  || (function() {
        var scripts = d.getElementsByTagName('script');
        return scripts[scripts.length - 1];
    })();

    // try to detect touch screen
    w.searx = {
        touch: (("ontouchstart" in w) || w.DocumentTouch && document instanceof DocumentTouch) || false,
        method: script.getAttribute('data-method'),
        autocompleter: script.getAttribute('data-autocompleter') === 'true',
        search_on_category_select: script.getAttribute('data-search-on-category-select') === 'true',
        infinite_scroll: script.getAttribute('data-infinite-scroll') === 'true',
        static_path: script.getAttribute('data-static-path'),
        translations: JSON.parse(script.getAttribute('data-translations')),
    };

    // update the css
    d.getElementsByTagName("html")[0].className = (w.searx.touch)?"js touch":"js";
})(window, document);