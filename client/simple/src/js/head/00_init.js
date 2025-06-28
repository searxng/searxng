/* SPDX-License-Identifier: AGPL-3.0-or-later */
((w, d) => {
  // add data- properties
  const getLastScriptElement = () => {
    const scripts = d.getElementsByTagName("script");
    return scripts[scripts.length - 1];
  };

  const script = d.currentScript || getLastScriptElement();

  w.searxng = {
    settings: JSON.parse(atob(script.getAttribute("client_settings")))
  };

  // update the css
  const htmlElement = d.getElementsByTagName("html")[0];
  htmlElement.classList.remove("no-js");
  htmlElement.classList.add("js");
})(window, document);
