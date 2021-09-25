(function (w, d, searx) {
    'use strict';

    searx.ready(function() {
        let engine_descriptions = null;
        function load_engine_descriptions() {
            if (engine_descriptions == null) {
                searx.http("GET", "engine_descriptions.json").then(function(content) {
                    engine_descriptions = JSON.parse(content);
                    for (const [engine_name, description] of Object.entries(engine_descriptions)) {
                        let elements = d.querySelectorAll('[data-engine-name="' + engine_name + '"] .engine-description');
                        for(const element of elements) {
                            let source = ' (<i>' + searx.translations['Source'] + ':&nbsp;' + description[1] + '</i>)';
                            element.innerHTML = description[0] + source;
                        }
                    }
                });
            }
        }

        if (d.querySelector('body[class="preferences_endpoint"]')) {
            for(const el of d.querySelectorAll('[data-engine-name]')) {
                searx.on(el, 'mouseenter', load_engine_descriptions);
            }
        }
    });
})(window, document, window.searx);
