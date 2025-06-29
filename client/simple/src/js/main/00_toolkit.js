/**
 * @license
 * (C) Copyright Contributors to the SearXNG project.
 * (C) Copyright Contributors to the searx project (2014 - 2021).
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */
window.searxng = ((w, d) => {
  // not invented here toolkit with bugs fixed elsewhere
  // purposes : be just good enough and as small as possible

  // from https://plainjs.com/javascript/events/live-binding-event-handlers-14/
  if (w.Element) {
    ((ElementPrototype) => {
      ElementPrototype.matches =
        ElementPrototype.matches ||
        ElementPrototype.matchesSelector ||
        ElementPrototype.webkitMatchesSelector ||
        ElementPrototype.msMatchesSelector ||
        function (selector) {
          const nodes = (this.parentNode || this.document).querySelectorAll(selector);
          let i = -1;
          while (nodes[++i] && nodes[i] !== this);
          return !!nodes[i];
        };
    })(Element.prototype);
  }

  function callbackSafe(callback, el, e) {
    try {
      callback.call(el, e);
    } catch (exception) {
      console.log(exception);
    }
  }

  const searxng = window.searxng || {};

  searxng.on = (obj, eventType, callback, useCapture) => {
    useCapture = useCapture || false;
    if (typeof obj !== "string") {
      // obj HTMLElement, HTMLDocument
      obj.addEventListener(eventType, callback, useCapture);
    } else {
      // obj is a selector
      d.addEventListener(
        eventType,
        (e) => {
          let el = e.target || e.srcElement;
          let found = false;

          while (el?.matches && el !== d) {
            found = el.matches(obj);

            if (found) break;

            el = el.parentElement;
          }

          if (found) {
            callbackSafe(callback, el, e);
          }
        },
        useCapture
      );
    }
  };

  searxng.ready = (callback) => {
    if (document.readyState !== "loading") {
      callback.call(w);
    } else {
      w.addEventListener("DOMContentLoaded", callback.bind(w));
    }
  };

  searxng.http = (method, url, data = null) =>
    new Promise((resolve, reject) => {
      try {
        const req = new XMLHttpRequest();
        req.open(method, url, true);
        req.timeout = 20000;

        // On load
        req.onload = () => {
          if (req.status === 200) {
            resolve(req.response, req.responseType);
          } else {
            reject(Error(req.statusText));
          }
        };

        // Handle network errors
        req.onerror = () => {
          reject(Error("Network Error"));
        };

        req.onabort = () => {
          reject(Error("Transaction is aborted"));
        };

        req.ontimeout = () => {
          reject(Error("Timeout"));
        };

        // Make the request
        if (data) {
          req.send(data);
        } else {
          req.send();
        }
      } catch (ex) {
        reject(ex);
      }
    });

  searxng.loadStyle = (src) => {
    const path = `${searxng.settings.theme_static_path}/${src}`;
    const id = `style_${src.replace(".", "_")}`;
    let s = d.getElementById(id);
    if (s === null) {
      s = d.createElement("link");
      s.setAttribute("id", id);
      s.setAttribute("rel", "stylesheet");
      s.setAttribute("type", "text/css");
      s.setAttribute("href", path);
      d.body.appendChild(s);
    }
  };

  searxng.loadScript = (src, callback) => {
    const path = `${searxng.settings.theme_static_path}/${src}`;
    const id = `script_${src.replace(".", "_")}`;
    let s = d.getElementById(id);
    if (s === null) {
      s = d.createElement("script");
      s.setAttribute("id", id);
      s.setAttribute("src", path);
      s.onload = callback;
      s.onerror = () => {
        s.setAttribute("error", "1");
      };
      d.body.appendChild(s);
    } else if (!s.hasAttribute("error")) {
      try {
        callback.apply(s, []);
      } catch (exception) {
        console.log(exception);
      }
    } else {
      console.log(`callback not executed : script '${path}' not loaded.`);
    }
  };

  searxng.insertBefore = (newNode, referenceNode) => {
    referenceNode.parentNode.insertBefore(newNode, referenceNode);
  };

  searxng.insertAfter = (newNode, referenceNode) => {
    referenceNode.parentNode.insertAfter(newNode, referenceNode.nextSibling);
  };

  searxng.on(".close", "click", function () {
    this.parentNode.classList.add("invisible");
  });

  function getEndpoint() {
    for (const className of d.getElementsByTagName("body")[0].classList.values()) {
      if (className.endsWith("_endpoint")) {
        return className.split("_")[0];
      }
    }
    return "";
  }

  searxng.endpoint = getEndpoint();

  return searxng;
})(window, document);
