/* SPDX-License-Identifier: AGPL-3.0-or-later */
(function (w, d, searxng) {
  'use strict';

  if (searxng.endpoint !== 'preferences') {
    return;
  }

  searxng.ready(function () {
    let engine_descriptions = null;
    function load_engine_descriptions () {
      if (engine_descriptions == null) {
        searxng.http("GET", "engine_descriptions.json").then(function (content) {
          engine_descriptions = JSON.parse(content);
          for (const [engine_name, description] of Object.entries(engine_descriptions)) {
            let elements = d.querySelectorAll('[data-engine-name="' + engine_name + '"] .engine-description');
            for (const element of elements) {
              let source = ' (<i>' + searxng.settings.translations.Source + ':&nbsp;' + description[1] + '</i>)';
              element.innerHTML = description[0] + source;
            }
          }
        });
      }
    }

    for (const el of d.querySelectorAll('[data-engine-name]')) {
      searxng.on(el, 'mouseenter', load_engine_descriptions);
    }

    const enableAllEngines = d.querySelectorAll(".enable-all-engines");
    const disableAllEngines = d.querySelectorAll(".disable-all-engines");
    const engineToggles = d.querySelectorAll('tbody input[type=checkbox][class~=checkbox-onoff]');
    const toggleEngines = (enable) => {
      for (const el of engineToggles) {
        // check if element visible, so that only engines of the current category are modified
        if (el.offsetParent !== null) el.checked = !enable;
      }
    };
    for (const el of enableAllEngines) {
      searxng.on(el, 'click', () => toggleEngines(true));
    }
    for (const el of disableAllEngines) {
      searxng.on(el, 'click', () => toggleEngines(false));
    }

    const copyHashButton = d.querySelector("#copy-hash");
    searxng.on(copyHashButton, 'click', (e) => {
      e.preventDefault();
      navigator.clipboard.writeText(copyHashButton.dataset.hash);
      copyHashButton.innerText = copyHashButton.dataset.copiedText;
    });
  });
})(window, document, window.searxng);
