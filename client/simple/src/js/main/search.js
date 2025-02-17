/* SPDX-License-Identifier: AGPL-3.0-or-later */
/* exported AutoComplete */

import AutoComplete from  "../../../node_modules/autocomplete-js/dist/autocomplete.js";

(function (w, d, searxng) {
  'use strict';

  var qinput_id = "q", qinput;

  const isMobile = window.matchMedia("only screen and (max-width: 50em)").matches;

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
    cs.addEventListener('click', function (ev) {
      qinput.value = '';
      qinput.focus();
      updateClearButton();
      ev.preventDefault();
    });
    qinput.addEventListener('input', updateClearButton, false);
  }

  searxng.ready(function () {
    qinput = d.getElementById(qinput_id);

    if (qinput !== null) {
      // clear button
      createClearButton(qinput);

      // autocompleter
      if (searxng.settings.autocomplete) {
        searxng.autocomplete = AutoComplete.call(w, {
          Url: "./autocompleter",
          EmptyMessage: searxng.settings.translations.no_item_found,
          HttpMethod: searxng.settings.method,
          HttpHeaders: {
            "Content-type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest"
          },
          MinChars: searxng.settings.autocomplete_min,
          Delay: 300,
          _Position: function () {},
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
          _Select: function (item) {
            AutoComplete.defaults._Select.call(this, item);
            var form = item.closest('form');
            if (form) {
              form.submit();
            }
          },
          _MinChars: function () {
            if (this.Input.value.indexOf('!') > -1) {
              return 0;
            } else {
              return AutoComplete.defaults._MinChars.call(this);
            }
          },
          KeyboardMappings: Object.assign({}, AutoComplete.defaults.KeyboardMappings, {
            "KeyUpAndDown_up": Object.assign({}, AutoComplete.defaults.KeyboardMappings.KeyUpAndDown_up, {
              Callback: function (event) {
                AutoComplete.defaults.KeyboardMappings.KeyUpAndDown_up.Callback.call(this, event);
                var liActive = this.DOMResults.querySelector("li.active");
                if (liActive) {
                  AutoComplete.defaults._Select.call(this, liActive);
                }
              },
            }),
            "Tab": Object.assign({}, AutoComplete.defaults.KeyboardMappings.Enter, {
              Conditions: [{
                Is: 9,
                Not: false
              }],
              Callback: function (event) {
                if (this.DOMResults.getAttribute("class").indexOf("open") != -1) {
                  var liActive = this.DOMResults.querySelector("li.active");
                  if (liActive !== null) {
                    AutoComplete.defaults._Select.call(this, liActive);
                    event.preventDefault();
                  }
                }
              },
            })
          }),
        }, "#" + qinput_id);
      }

      /*
        Monkey patch autocomplete.js to fix a bug
        With the POST method, the values are not URL encoded: query like "1 + 1" are sent as "1  1" since space are URL encoded as plus.
        See HTML specifications:
        * HTML5: https://url.spec.whatwg.org/#concept-urlencoded-serializer
        * HTML4: https://www.w3.org/TR/html401/interact/forms.html#h-17.13.4.1

        autocomplete.js does not URL encode the name and values:
        https://github.com/autocompletejs/autocomplete.js/blob/87069524f3b95e68f1b54d8976868e0eac1b2c83/src/autocomplete.ts#L665

        The monkey patch overrides the compiled version of the ajax function.
        See https://github.com/autocompletejs/autocomplete.js/blob/87069524f3b95e68f1b54d8976868e0eac1b2c83/dist/autocomplete.js#L143-L158
        The patch changes only the line 156 from
          params.Request.send(params._QueryArg() + "=" + params._Pre());
        to
          params.Request.send(encodeURIComponent(params._QueryArg()) + "=" + encodeURIComponent(params._Pre()));

        Related to:
        * https://github.com/autocompletejs/autocomplete.js/issues/78
        * https://github.com/searxng/searxng/issues/1695
       */
      AutoComplete.prototype.ajax = function (params, request, timeout) {
        if (timeout === void 0) { timeout = true; }
        if (params.$AjaxTimer) {
          window.clearTimeout(params.$AjaxTimer);
        }
        if (timeout === true) {
          params.$AjaxTimer = window.setTimeout(AutoComplete.prototype.ajax.bind(null, params, request, false), params.Delay);
        } else {
          if (params.Request) {
            params.Request.abort();
          }
          params.Request = request;
          params.Request.send(encodeURIComponent(params._QueryArg()) + "=" + encodeURIComponent(params._Pre()));
        }
      };

      if (!isMobile && document.querySelector('.index_endpoint')) {
        qinput.focus();
      }
    }

    // Additionally to searching when selecting a new category, we also
    // automatically start a new search request when the user changes a search
    // filter (safesearch, time range or language) (this requires JavaScript
    // though)
    if (
      qinput !== null
        && searxng.settings.search_on_category_select
      // If .search_filters is undefined (invisible) we are on the homepage and
      // hence don't have to set any listeners
        && d.querySelector(".search_filters") != null
    ) {
      searxng.on(d.getElementById('safesearch'), 'change', submitIfQuery);
      searxng.on(d.getElementById('time_range'), 'change', submitIfQuery);
      searxng.on(d.getElementById('language'), 'change', submitIfQuery);
    }

    const categoryButtons = d.querySelectorAll("button.category_button");
    for (let button of categoryButtons) {
      searxng.on(button, 'click', (event) => {
        if (event.shiftKey) {
          event.preventDefault();
          button.classList.toggle("selected");
          return;
        }

        // manually deselect the old selection when a new category is selected
        const selectedCategories = d.querySelectorAll("button.category_button.selected");
        for (let categoryButton of selectedCategories) {
          categoryButton.classList.remove("selected");
        }
        button.classList.add("selected");
      })
    }

    // override form submit action to update the actually selected categories
    const form = d.querySelector("#search");
    if (form != null) {
      searxng.on(form, 'submit', (event) => {
        event.preventDefault();
        const categoryValuesInput = d.querySelector("#selected-categories");
        if (categoryValuesInput) {
          let categoryValues = [];
          for (let categoryButton of categoryButtons) {
            if (categoryButton.classList.contains("selected")) {
              categoryValues.push(categoryButton.name.replace("category_", ""));
            }
          }
          categoryValuesInput.value = categoryValues.join(",");
        }
        form.submit();
      });
    }
  });

})(window, document, window.searxng);
