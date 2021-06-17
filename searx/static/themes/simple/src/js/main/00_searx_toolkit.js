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
* (C) 2017 by Alexandre Flament, <alex@al-f.net>
*
*/
window.searx = (function(w, d) {

  'use strict';

  // not invented here tookit with bugs fixed elsewhere
  // purposes : be just good enough and as small as possible

  // from https://plainjs.com/javascript/events/live-binding-event-handlers-14/
  if (w.Element) {
    (function(ElementPrototype) {
      ElementPrototype.matches = ElementPrototype.matches ||
      ElementPrototype.matchesSelector ||
      ElementPrototype.webkitMatchesSelector ||
      ElementPrototype.msMatchesSelector ||
      function(selector) {
        var node = this, nodes = (node.parentNode || node.document).querySelectorAll(selector), i = -1;
        while (nodes[++i] && nodes[i] != node);
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

  var searx = window.searx || {};

  searx.on = function(obj, eventType, callback, useCapture) {
    useCapture = useCapture || false;
    if (typeof obj !== 'string') {
      // obj HTMLElement, HTMLDocument
      obj.addEventListener(eventType, callback, useCapture);
    } else {
      // obj is a selector
      d.addEventListener(eventType, function(e) {
        var el = e.target || e.srcElement, found = false;
        while (el && el.matches && el !== d && !(found = el.matches(obj))) el = el.parentElement;
        if (found) callbackSafe(callback, el, e);
      }, useCapture);
    }
  };

  searx.ready = function(callback) {
    if (document.readyState != 'loading') {
      callback.call(w);
    } else {
      w.addEventListener('DOMContentLoaded', callback.bind(w));
    }
  };

  searx.http = function(method, url, callback) {
    var req = new XMLHttpRequest(),
    resolve = function() {},
    reject = function() {},
    promise = {
      then: function(callback) { resolve = callback; return promise; },
      catch: function(callback) { reject = callback; return promise; }
    };

    try {
      req.open(method, url, true);

      // On load
      req.onload = function() {
        if (req.status == 200) {
          resolve(req.response, req.responseType);
        } else {
          reject(Error(req.statusText));
        }
      };

      // Handle network errors
      req.onerror = function() {
        reject(Error("Network Error"));
      };

      req.onabort = function() {
        reject(Error("Transaction is aborted"));
      };

      // Make the request
      req.send();
    } catch (ex) {
      reject(ex);
    }

    return promise;
  };

  searx.loadStyle = function(src) {
    var path = searx.static_path + src,
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

  searx.loadScript = function(src, callback) {
    var path = searx.static_path + src,
    id = "script_" + src.replace('.', '_'),
    s = d.getElementById(id);
    if (s === null) {
      s = d.createElement('script');
      s.setAttribute('id', id);
      s.setAttribute('src', path);
      s.onload = callback;
      s.onerror = function() {
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

  searx.insertBefore = function (newNode, referenceNode) {
    element.parentNode.insertBefore(newNode, referenceNode);
  };

  searx.insertAfter = function(newNode, referenceNode) {
    referenceNode.parentNode.insertBefore(newNode, referenceNode.nextSibling);
  };  

  searx.on('.close', 'click', function(e) {
    var el = e.target || e.srcElement;
    this.parentNode.classList.add('invisible');
  });
  
  return searx;
})(window, document);
