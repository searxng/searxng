/**
 * @license
 * (C) Copyright Contributors to the SearXNG project.
 * (C) Copyright Contributors to the searx project (2014 - 2021).
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */
window.searxng = (function (w, d) {

  'use strict';

  // not invented here tookit with bugs fixed elsewhere
  // purposes : be just good enough and as small as possible

  // from https://plainjs.com/javascript/events/live-binding-event-handlers-14/
  if (w.Element) {
    (function (ElementPrototype) {
      ElementPrototype.matches = ElementPrototype.matches ||
      ElementPrototype.matchesSelector ||
      ElementPrototype.webkitMatchesSelector ||
      ElementPrototype.msMatchesSelector ||
      function (selector) {
        var node = this, nodes = (node.parentNode || node.document).querySelectorAll(selector), i = -1;
        while (nodes[++i] && nodes[i] != node);
        return !!nodes[i];
      };
    })(Element.prototype);
  }

  function callbackSafe (callback, el, e) {
    try {
      callback.call(el, e);
    } catch (exception) {
      console.log(exception);
    }
  }

  var searxng = window.searxng || {};

  searxng.on = function (obj, eventType, callback, useCapture) {
    useCapture = useCapture || false;
    if (typeof obj !== 'string') {
      // obj HTMLElement, HTMLDocument
      obj.addEventListener(eventType, callback, useCapture);
    } else {
      // obj is a selector
      d.addEventListener(eventType, function (e) {
        var el = e.target || e.srcElement, found = false;
        while (el && el.matches && el !== d && !(found = el.matches(obj))) el = el.parentElement;
        if (found) callbackSafe(callback, el, e);
      }, useCapture);
    }
  };

  searxng.ready = function (callback) {
    if (document.readyState != 'loading') {
      callback.call(w);
    } else {
      w.addEventListener('DOMContentLoaded', callback.bind(w));
    }
  };

  searxng.http = function (method, url, data = null) {
    return new Promise(function (resolve, reject) {
      try {
        var req = new XMLHttpRequest();
        req.open(method, url, true);
        req.timeout = 20000;

        // On load
        req.onload = function () {
          if (req.status == 200) {
            resolve(req.response, req.responseType);
          } else {
            reject(Error(req.statusText));
          }
        };

        // Handle network errors
        req.onerror = function () {
          reject(Error("Network Error"));
        };

        req.onabort = function () {
          reject(Error("Transaction is aborted"));
        };

        req.ontimeout = function () {
          reject(Error("Timeout"));
        }

        // Make the request
        if (data) {
          req.send(data)
        } else {
          req.send();
        }
      } catch (ex) {
        reject(ex);
      }
    });
  };

  searxng.loadStyle = function (src) {
    var path = searxng.settings.theme_static_path + "/" + src,
      id = "style_" + src.replace('.', '_'),
      s = d.getElementById(id);
    if (s === null) {
      s = d.createElement('link');
      s.setAttribute('id', id);
      s.setAttribute('rel', 'stylesheet');
      s.setAttribute('type', 'text/css');
      s.setAttribute('href', path);
      d.body.appendChild(s);
    }
  };

  searxng.loadScript = function (src, callback) {
    var path = searxng.settings.theme_static_path + "/" + src,
      id = "script_" + src.replace('.', '_'),
      s = d.getElementById(id);
    if (s === null) {
      s = d.createElement('script');
      s.setAttribute('id', id);
      s.setAttribute('src', path);
      s.onload = callback;
      s.onerror = function () {
        s.setAttribute('error', '1');
      };
      d.body.appendChild(s);
    } else if (!s.hasAttribute('error')) {
      try {
        callback.apply(s, []);
      } catch (exception) {
        console.log(exception);
      }
    } else {
      console.log("callback not executed : script '" + path + "' not loaded.");
    }
  };

  searxng.insertBefore = function (newNode, referenceNode) {
    referenceNode.parentNode.insertBefore(newNode, referenceNode);
  };

  searxng.insertAfter = function (newNode, referenceNode) {
    referenceNode.parentNode.insertAfter(newNode, referenceNode.nextSibling);
  };

  searxng.on('.close', 'click', function () {
    this.parentNode.classList.add('invisible');
  });

  function getEndpoint () {
    for (var className of d.getElementsByTagName('body')[0].classList.values()) {
      if (className.endsWith('_endpoint')) {
        return className.split('_')[0];
      }
    }
    return '';
  }

  searxng.endpoint = getEndpoint();

  return searxng;
})(window, document);
