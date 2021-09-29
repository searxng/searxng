/**
* searxng is free software: you can redistribute it and/or modify
* it under the terms of the GNU Affero General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
*
* searxng is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU Affero General Public License for more details.
*
* You should have received a copy of the GNU Affero General Public License
* along with searxng. If not, see < http://www.gnu.org/licenses/ >.
*
* (C) 2017 by Alexandre Flament, <alex@al-f.net>
*/
/* global AutoComplete */
(function(w, d, searxng) {
  'use strict';

  var firstFocus = true, qinput_id = "q", qinput;

  function placeCursorAtEnd(element) {
    if (element.setSelectionRange) {
      var len = element.value.length;
      element.setSelectionRange(len, len);
    }
  }

  function submitIfQuery() {
    if (qinput.value.length  > 0) {
      var search = document.getElementById('search');
      setTimeout(search.submit.bind(search), 0);
    }
  }

  function createClearButton(qinput) {
    var cs = document.getElementById('clear_search');
    var updateClearButton = function() {
      if (qinput.value.length === 0) {
	cs.classList.add("empty");
      } else {
	cs.classList.remove("empty");
      }
    };

    // update status, event listener
    updateClearButton();
    cs.addEventListener('click', function() {
      qinput.value='';
      qinput.focus();
      updateClearButton();
    });
    qinput.addEventListener('keyup', updateClearButton, false);
  }

  searxng.ready(function() {
    qinput = d.getElementById(qinput_id);

    function placeCursorAtEndOnce() {
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
        }, "#" + qinput_id);

        // hack, see : https://github.com/autocompletejs/autocomplete.js/issues/37
        w.addEventListener('resize', function() {
          var event = new CustomEvent("position");
          qinput.dispatchEvent(event);
        });
      }

      qinput.addEventListener('focus', placeCursorAtEndOnce, false);
      qinput.focus();
    }

    // vanilla js version of search_on_category_select.js
    if (qinput !== null && d.querySelector('.help') != null && searxng.search_on_category_select) {
      d.querySelector('.help').className='invisible';

      searxng.on('#categories input', 'change', function() {
        var i, categories = d.querySelectorAll('#categories input[type="checkbox"]');
        for(i=0; i<categories.length; i++) {
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

      searxng.on(d.getElementById('time_range'), 'change', submitIfQuery);
      searxng.on(d.getElementById('language'), 'change', submitIfQuery);
    }

  });

})(window, document, window.searxng);
