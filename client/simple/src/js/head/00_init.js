/* SPDX-License-Identifier: AGPL-3.0-or-later */
((w, d) => {
  // add data- properties
  var script =
    d.currentScript ||
    (() => {
      var scripts = d.getElementsByTagName("script");
      return scripts[scripts.length - 1];
    })();

  w.searxng = {
    settings: JSON.parse(atob(script.getAttribute("client_settings")))
  };

  // update the css
  const htmlElement = d.getElementsByTagName("html")[0];
  htmlElement.classList.remove("no-js");
  htmlElement.classList.add("js");
})(window, document);
