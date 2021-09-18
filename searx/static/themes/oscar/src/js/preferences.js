$(document).ready(function(){
    let engine_descriptions = null;
    function load_engine_descriptions() {
        if (engine_descriptions == null) {
            $.ajax("engine_descriptions.json", dataType="json").done(function(data) {
                engine_descriptions = data;
                for (const [engine_name, description] of Object.entries(data)) {
                    let elements = $('[data-engine-name="' + engine_name + '"] .description');
                    for(const element of elements) {
                        let source = ' (<i>' + searx.translations['Source'] + ':&nbsp;' + description[1] + '</i>)';
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
