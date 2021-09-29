/**
 * searxng is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * searxng is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with searxng. If not, see < http://www.gnu.org/licenses/ >.
 *
 * (C) 2019 by Alexandre Flament
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
        method: script.getAttribute('data-method'),
        translations: JSON.parse(script.getAttribute('data-translations'))
    };
})(document);
