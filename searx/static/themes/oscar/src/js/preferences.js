/**
 * @license
 * (C) Copyright Contributors to the SearXNG project.
 * (C) Copyright Contributors to the searx project (2014 - 2021).
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

$(document).ready(function(){
    let engine_descriptions = null;
    function load_engine_descriptions() {
        if (engine_descriptions == null) {
            $.ajax("engine_descriptions.json", dataType="json").done(function(data) {
                engine_descriptions = data;
                for (const [engine_name, description] of Object.entries(data)) {
                    let elements = $('[data-engine-name="' + engine_name + '"] .description');
                    for(const element of elements) {
                        let source = ' (<i>' + searxng.translations.Source + ':&nbsp;' + description[1] + '</i>)';
                        element.innerHTML = description[0] + source;
                    }
                }
            });
        }
    }

    if (document.querySelector('body[class="preferences_endpoint"]')) {
        $('[data-engine-name]').hover(function() {
            load_engine_descriptions();
        });
    }
});
