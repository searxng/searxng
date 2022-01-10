/* SPDX-License-Identifier: AGPL-3.0-or-later */
/* global AutoComplete */
(function (w, d, searxng) {
  'use strict';

  var firstFocus = true, qinput_id = "q", qinput;

  function placeCursorAtEnd (element) {
    if (element.setSelectionRange) {
      var len = element.value.length;
      element.setSelectionRange(len, len);
    }
  }

  function submitIfQuery () {
    if (qinput.value.length  > 0) {
      var search = document.getElementById('search');
      setTimeout(search.submit.bind(search), 0);
    }
  }

  function createClearButton (qinput) {
    var cs = document.getElementById('clear_search');
    var updateClearButton = function () {
      if (qinput.value.length === 0) {
        cs.classList.add("empty");
      } else {
        cs.classList.remove("empty");
      }
    };

    // update status, event listener
    updateClearButton();
    cs.addEventListener('click', function () {
      qinput.value = '';
      qinput.focus();
      updateClearButton();
    });
    qinput.addEventListener('keyup', updateClearButton, false);
  }

  searxng.ready(function () {
    qinput = d.getElementById(qinput_id);

    function placeCursorAtEndOnce () {
      if (firstFocus) {
        placeCursorAtEnd(qinput);
        firstFocus = false;
      } else {
        // e.preventDefault();
      }
    }

    if (qinput !== null) {
      // clear button
      createClearButton(qinput);

      // autocompleter
      if (searxng.autocompleter) {
        searxng.autocomplete = AutoComplete.call(w, {
          Url: "./autocompleter",
          EmptyMessage: searxng.translations.no_item_found,
          HttpMethod: searxng.method,
          HttpHeaders: {
            "Content-type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest"
          },
          MinChars: 4,
          Delay: 300,
          _Position: function () {
            this.DOMResults.setAttribute("class", "autocomplete");
            this.DOMResults.style.top = (this.Input.offsetTop + this.Input.offsetHeight) + "px";
            this.DOMResults.style.left = this.Input.offsetLeft + "px";
            this.DOMResults.style.width = this.Input.clientWidth + "px";
          },
          _Open: function () {
            var params = this;
            Array.prototype.forEach.call(this.DOMResults.getElementsByTagName("li"), function (li) {
              if (li.getAttribute("class") != "locked") {
                li.onmousedown = function () {
                  params._Select(li);
                };
              }
            });
          },
        }, "#" + qinput_id);

        // hack, see : https://github.com/autocompletejs/autocomplete.js/issues/37
        w.addEventListener('resize', function () {
          var event = new CustomEvent("position");
          qinput.dispatchEvent(event);
        });
      }

      qinput.addEventListener('focus', placeCursorAtEndOnce, false);
      qinput.focus();
    }

    // vanilla js version of search_on_category_select.js
    if (qinput !== null && d.querySelector('.help') != null && searxng.search_on_category_select) {
      d.querySelector('.help').className = 'invisible';

      searxng.on('#categories input', 'change', function () {
        var i, categories = d.querySelectorAll('#categories input[type="checkbox"]');
        for (i = 0; i < categories.length; i++) {
          if (categories[i] !== this && categories[i].checked) {
            categories[i].click();
          }
        }
        if (! this.checked) {
          this.click();
        }
        submitIfQuery();
        return false;
      });

      searxng.on(d.getElementById('safesearch'), 'change', submitIfQuery);
      searxng.on(d.getElementById('time_range'), 'change', submitIfQuery);
      searxng.on(d.getElementById('language'), 'change', submitIfQuery);
    }

  });

})(window, document, window.searxng);
