/* SPDX-License-Identifier: AGPL-3.0-or-later */
/* global searxng */

searxng.ready(function () {

  function isElementInDetail (el) {
    while (el !== undefined) {
      if (el.classList.contains('detail')) {
        return true;
      }
      if (el.classList.contains('result')) {
        // we found a result, no need to go to the root of the document:
        // el is not inside a <div class="detail"> element
        return false;
      }
      el = el.parentNode;
    }
    return false;
  }

  function getResultElement (el) {
    while (el !== undefined) {
      if (el.classList.contains('result')) {
        return el;
      }
      el = el.parentNode;
    }
    return undefined;
  }

  function isImageResult (resultElement) {
    return resultElement && resultElement.classList.contains('result-images');
  }

  searxng.on('.result', 'click', function (e) {
    if (!isElementInDetail(e.target)) {
      highlightResult(this)(true, true);
      let resultElement = getResultElement(e.target);
      if (isImageResult(resultElement)) {
        e.preventDefault();
        searxng.selectImage(resultElement);
      }
    }
  });

  searxng.on('.result a', 'focus', function (e) {
    if (!isElementInDetail(e.target)) {
      let resultElement = getResultElement(e.target);
      if (resultElement && resultElement.getAttribute("data-vim-selected") === null) {
        highlightResult(resultElement)(true);
      }
      if (isImageResult(resultElement)) {
        searxng.selectImage(resultElement);
      }
    }
  }, true);

  var vimKeys = {
    27: {
      key: 'Escape',
      fun: removeFocus,
      des: 'remove focus from the focused input',
      cat: 'Control'
    },
    73: {
      key: 'i',
      fun: searchInputFocus,
      des: 'focus on the search input',
      cat: 'Control'
    },
    66: {
      key: 'b',
      fun: scrollPage(-window.innerHeight),
      des: 'scroll one page up',
      cat: 'Navigation'
    },
    70: {
      key: 'f',
      fun: scrollPage(window.innerHeight),
      des: 'scroll one page down',
      cat: 'Navigation'
    },
    85: {
      key: 'u',
      fun: scrollPage(-window.innerHeight / 2),
      des: 'scroll half a page up',
      cat: 'Navigation'
    },
    68: {
      key: 'd',
      fun: scrollPage(window.innerHeight / 2),
      des: 'scroll half a page down',
      cat: 'Navigation'
    },
    71: {
      key: 'g',
      fun: scrollPageTo(-document.body.scrollHeight, 'top'),
      des: 'scroll to the top of the page',
      cat: 'Navigation'
    },
    86: {
      key: 'v',
      fun: scrollPageTo(document.body.scrollHeight, 'bottom'),
      des: 'scroll to the bottom of the page',
      cat: 'Navigation'
    },
    75: {
      key: 'k',
      fun: highlightResult('up'),
      des: 'select previous search result',
      cat: 'Results'
    },
    74: {
      key: 'j',
      fun: highlightResult('down'),
      des: 'select next search result',
      cat: 'Results'
    },
    80: {
      key: 'p',
      fun: GoToPreviousPage(),
      des: 'go to previous page',
      cat: 'Results'
    },
    78: {
      key: 'n',
      fun: GoToNextPage(),
      des: 'go to next page',
      cat: 'Results'
    },
    79: {
      key: 'o',
      fun: openResult(false),
      des: 'open search result',
      cat: 'Results'
    },
    84: {
      key: 't',
      fun: openResult(true),
      des: 'open the result in a new tab',
      cat: 'Results'
    },
    82: {
      key: 'r',
      fun: reloadPage,
      des: 'reload page from the server',
      cat: 'Control'
    },
    72: {
      key: 'h',
      fun: toggleHelp,
      des: 'toggle help window',
      cat: 'Other'
    }
  };

  if (searxng.settings.hotkeys) {
    searxng.on(document, "keydown", function (e) {
      // check for modifiers so we don't break browser's hotkeys
      if (Object.prototype.hasOwnProperty.call(vimKeys, e.keyCode) && !e.ctrlKey && !e.altKey && !e.shiftKey && !e.metaKey) {
        var tagName = e.target.tagName.toLowerCase();
        if (e.keyCode === 27) {
          vimKeys[e.keyCode].fun(e);
        } else {
          if (e.target === document.body || tagName === 'a' || tagName === 'button') {
            e.preventDefault();
            vimKeys[e.keyCode].fun();
          }
        }
      }
    });
  }

  function highlightResult (which) {
    return function (noScroll, keepFocus) {
      var current = document.querySelector('.result[data-vim-selected]'),
        effectiveWhich = which;
      if (current === null) {
        // no selection : choose the first one
        current = document.querySelector('.result');
        if (current === null) {
          // no first one : there are no results
          return;
        }
        // replace up/down actions by selecting first one
        if (which === "down" || which === "up") {
          effectiveWhich = current;
        }
      }

      var next, results = document.querySelectorAll('.result');

      if (typeof effectiveWhich !== 'string') {
        next = effectiveWhich;
      } else {
        switch (effectiveWhich) {
        case 'visible':
          var top = document.documentElement.scrollTop || document.body.scrollTop;
          var bot = top + document.documentElement.clientHeight;

          for (var i = 0; i < results.length; i++) {
            next = results[i];
            var etop = next.offsetTop;
            var ebot = etop + next.clientHeight;

            if ((ebot <= bot) && (etop > top)) {
              break;
            }
          }
          break;
        case 'down':
          next = current.nextElementSibling;
          if (next === null) {
            next = results[0];
          }
          break;
        case 'up':
          next = current.previousElementSibling;
          if (next === null) {
            next = results[results.length - 1];
          }
          break;
        case 'bottom':
          next = results[results.length - 1];
          break;
        case 'top':
          /* falls through */
        default:
          next = results[0];
        }
      }

      if (next) {
        current.removeAttribute('data-vim-selected');
        next.setAttribute('data-vim-selected', 'true');
        if (!keepFocus) {
          var link = next.querySelector('h3 a') || next.querySelector('a');
          if (link !== null) {
            link.focus();
          }
        }
        if (!noScroll) {
          scrollPageToSelected();
        }
      }
    };
  }

  function reloadPage () {
    document.location.reload(true);
  }

  function removeFocus (e) {
    const tagName = e.target.tagName.toLowerCase();
    if (document.activeElement && (tagName === 'input' || tagName === 'select' || tagName === 'textarea')) {
      document.activeElement.blur();
    } else {
      searxng.closeDetail();
    }
  }

  function pageButtonClick (css_selector) {
    return function () {
      var button = document.querySelector(css_selector);
      if (button) {
        button.click();
      }
    };
  }

  function GoToNextPage () {
    return pageButtonClick('nav#pagination .next_page button[type="submit"]');
  }

  function GoToPreviousPage () {
    return pageButtonClick('nav#pagination .previous_page button[type="submit"]');
  }

  function scrollPageToSelected () {
    var sel = document.querySelector('.result[data-vim-selected]');
    if (sel === null) {
      return;
    }
    var wtop = document.documentElement.scrollTop || document.body.scrollTop,
      wheight = document.documentElement.clientHeight,
      etop = sel.offsetTop,
      ebot = etop + sel.clientHeight,
      offset = 120;
    // first element ?
    if ((sel.previousElementSibling === null) && (ebot < wheight)) {
      // set to the top of page if the first element
      // is fully included in the viewport
      window.scroll(window.scrollX, 0);
      return;
    }
    if (wtop > (etop - offset)) {
      window.scroll(window.scrollX, etop - offset);
    } else {
      var wbot = wtop + wheight;
      if (wbot < (ebot + offset)) {
        window.scroll(window.scrollX, ebot - wheight + offset);
      }
    }
  }

  function scrollPage (amount) {
    return function () {
      window.scrollBy(0, amount);
      highlightResult('visible')();
    };
  }

  function scrollPageTo (position, nav) {
    return function () {
      window.scrollTo(0, position);
      highlightResult(nav)();
    };
  }

  function searchInputFocus () {
    window.scrollTo(0, 0);
    var q = document.querySelector('#q');
    q.focus();
    if (q.setSelectionRange) {
      var len = q.value.length;
      q.setSelectionRange(len, len);
    }
  }

  function openResult (newTab) {
    return function () {
      var link = document.querySelector('.result[data-vim-selected] h3 a');
      if (link === null) {
        link = document.querySelector('.result[data-vim-selected] > a');
      }
      if (link !== null) {
        var url = link.getAttribute('href');
        if (newTab) {
          window.open(url);
        } else {
          window.location.href = url;
        }
      }
    };
  }

  function initHelpContent (divElement) {
    var categories = {};

    for (var k in vimKeys) {
      var key = vimKeys[k];
      categories[key.cat] = categories[key.cat] || [];
      categories[key.cat].push(key);
    }

    var sorted = Object.keys(categories).sort(function (a, b) {
      return categories[b].length - categories[a].length;
    });

    if (sorted.length === 0) {
      return;
    }

    var html = '<a href="#" class="close" aria-label="close" title="close">×</a>';
    html += '<h3>How to navigate searx with Vim-like hotkeys</h3>';
    html += '<table>';

    for (var i = 0; i < sorted.length; i++) {
      var cat = categories[sorted[i]];

      var lastCategory = i === (sorted.length - 1);
      var first = i % 2 === 0;

      if (first) {
        html += '<tr>';
      }
      html += '<td>';

      html += '<h4>' + cat[0].cat + '</h4>';
      html += '<ul class="list-unstyled">';

      for (var cj in cat) {
        html += '<li><kbd>' + cat[cj].key + '</kbd> ' + cat[cj].des + '</li>';
      }

      html += '</ul>';
      html += '</td>'; // col-sm-*

      if (!first || lastCategory) {
        html += '</tr>'; // row
      }
    }

    html += '</table>';

    divElement.innerHTML = html;
  }

  function toggleHelp () {
    var helpPanel = document.querySelector('#vim-hotkeys-help');
    if (helpPanel === undefined || helpPanel === null) {
      // first call
      helpPanel = document.createElement('div');
      helpPanel.id = 'vim-hotkeys-help';
      helpPanel.className = 'dialog-modal';
      initHelpContent(helpPanel);
      initHelpContent(helpPanel);
      initHelpContent(helpPanel);
      var body = document.getElementsByTagName('body')[0];
      body.appendChild(helpPanel);
    } else {
      // togggle hidden
      helpPanel.classList.toggle('invisible');
      return;
    }
  }

  searxng.scrollPageToSelected = scrollPageToSelected;
  searxng.selectNext = highlightResult('down');
  searxng.selectPrevious = highlightResult('up');
});
