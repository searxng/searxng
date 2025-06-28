/* SPDX-License-Identifier: AGPL-3.0-or-later */
/* global searxng */

searxng.ready(() => {
  function isElementInDetail(el) {
    while (el !== undefined) {
      if (el.classList.contains("detail")) {
        return true;
      }
      if (el.classList.contains("result")) {
        // we found a result, no need to go to the root of the document:
        // el is not inside a <div class="detail"> element
        return false;
      }
      el = el.parentNode;
    }
    return false;
  }

  function getResultElement(el) {
    while (el !== undefined) {
      if (el.classList.contains("result")) {
        return el;
      }
      el = el.parentNode;
    }
    return undefined;
  }

  function isImageResult(resultElement) {
    return resultElement?.classList.contains("result-images");
  }

  searxng.on(".result", "click", function (e) {
    if (!isElementInDetail(e.target)) {
      highlightResult(this)(true, true);
      const resultElement = getResultElement(e.target);
      if (isImageResult(resultElement)) {
        e.preventDefault();
        searxng.selectImage(resultElement);
      }
    }
  });

  searxng.on(
    ".result a",
    "focus",
    (e) => {
      if (!isElementInDetail(e.target)) {
        const resultElement = getResultElement(e.target);
        if (resultElement && resultElement.getAttribute("data-vim-selected") === null) {
          highlightResult(resultElement)(true);
        }
        if (isImageResult(resultElement)) {
          searxng.selectImage(resultElement);
        }
      }
    },
    true
  );

  /* common base for layouts */
  const baseKeyBinding = {
    Escape: {
      key: "ESC",
      fun: removeFocus,
      des: "remove focus from the focused input",
      cat: "Control"
    },
    c: {
      key: "c",
      fun: copyURLToClipboard,
      des: "copy url of the selected result to the clipboard",
      cat: "Results"
    },
    h: {
      key: "h",
      fun: toggleHelp,
      des: "toggle help window",
      cat: "Other"
    },
    i: {
      key: "i",
      fun: searchInputFocus,
      des: "focus on the search input",
      cat: "Control"
    },
    n: {
      key: "n",
      fun: GoToNextPage(),
      des: "go to next page",
      cat: "Results"
    },
    o: {
      key: "o",
      fun: openResult(false),
      des: "open search result",
      cat: "Results"
    },
    p: {
      key: "p",
      fun: GoToPreviousPage(),
      des: "go to previous page",
      cat: "Results"
    },
    r: {
      key: "r",
      fun: reloadPage,
      des: "reload page from the server",
      cat: "Control"
    },
    t: {
      key: "t",
      fun: openResult(true),
      des: "open the result in a new tab",
      cat: "Results"
    }
  };
  const keyBindingLayouts = {
    default: Object.assign(
      {
        /* SearXNG layout */
        ArrowLeft: {
          key: "←",
          fun: highlightResult("up"),
          des: "select previous search result",
          cat: "Results"
        },
        ArrowRight: {
          key: "→",
          fun: highlightResult("down"),
          des: "select next search result",
          cat: "Results"
        }
      },
      baseKeyBinding
    ),

    vim: Object.assign(
      {
        /* Vim-like Key Layout. */
        b: {
          key: "b",
          fun: scrollPage(-window.innerHeight),
          des: "scroll one page up",
          cat: "Navigation"
        },
        f: {
          key: "f",
          fun: scrollPage(window.innerHeight),
          des: "scroll one page down",
          cat: "Navigation"
        },
        u: {
          key: "u",
          fun: scrollPage(-window.innerHeight / 2),
          des: "scroll half a page up",
          cat: "Navigation"
        },
        d: {
          key: "d",
          fun: scrollPage(window.innerHeight / 2),
          des: "scroll half a page down",
          cat: "Navigation"
        },
        g: {
          key: "g",
          fun: scrollPageTo(-document.body.scrollHeight, "top"),
          des: "scroll to the top of the page",
          cat: "Navigation"
        },
        v: {
          key: "v",
          fun: scrollPageTo(document.body.scrollHeight, "bottom"),
          des: "scroll to the bottom of the page",
          cat: "Navigation"
        },
        k: {
          key: "k",
          fun: highlightResult("up"),
          des: "select previous search result",
          cat: "Results"
        },
        j: {
          key: "j",
          fun: highlightResult("down"),
          des: "select next search result",
          cat: "Results"
        },
        y: {
          key: "y",
          fun: copyURLToClipboard,
          des: "copy url of the selected result to the clipboard",
          cat: "Results"
        }
      },
      baseKeyBinding
    )
  };

  const keyBindings = keyBindingLayouts[searxng.settings.hotkeys] || keyBindingLayouts.default;

  searxng.on(document, "keydown", (e) => {
    // check for modifiers so we don't break browser's hotkeys
    if (
      // biome-ignore lint/suspicious/noPrototypeBuiltins: FIXME: support for Chromium 93-87, Firefox 92-78, Safari 15.4-14
      Object.prototype.hasOwnProperty.call(keyBindings, e.key) &&
      !e.ctrlKey &&
      !e.altKey &&
      !e.shiftKey &&
      !e.metaKey
    ) {
      const tagName = e.target.tagName.toLowerCase();
      if (e.key === "Escape") {
        keyBindings[e.key].fun(e);
      } else {
        if (e.target === document.body || tagName === "a" || tagName === "button") {
          e.preventDefault();
          keyBindings[e.key].fun();
        }
      }
    }
  });

  function highlightResult(which) {
    return (noScroll, keepFocus) => {
      let current = document.querySelector(".result[data-vim-selected]"),
        effectiveWhich = which;
      if (current === null) {
        // no selection : choose the first one
        current = document.querySelector(".result");
        if (current === null) {
          // no first one : there are no results
          return;
        }
        // replace up/down actions by selecting first one
        if (which === "down" || which === "up") {
          effectiveWhich = current;
        }
      }

      let next,
        results = document.querySelectorAll(".result");
      results = Array.from(results); // convert NodeList to Array for further use

      if (typeof effectiveWhich !== "string") {
        next = effectiveWhich;
      } else {
        switch (effectiveWhich) {
          case "visible": {
            const top = document.documentElement.scrollTop || document.body.scrollTop;
            const bot = top + document.documentElement.clientHeight;

            for (let i = 0; i < results.length; i++) {
              next = results[i];
              const etop = next.offsetTop;
              const ebot = etop + next.clientHeight;

              if (ebot <= bot && etop > top) {
                break;
              }
            }
            break;
          }
          case "down":
            next = results[results.indexOf(current) + 1] || current;
            break;
          case "up":
            next = results[results.indexOf(current) - 1] || current;
            break;
          case "bottom":
            next = results[results.length - 1];
            break;
          // biome-ignore lint/complexity/noUselessSwitchCase: fallthrough is intended
          case "top":
          /* falls through */
          default:
            next = results[0];
        }
      }

      if (next) {
        current.removeAttribute("data-vim-selected");
        next.setAttribute("data-vim-selected", "true");
        if (!keepFocus) {
          const link = next.querySelector("h3 a") || next.querySelector("a");
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

  function reloadPage() {
    document.location.reload(true);
  }

  function removeFocus(e) {
    const tagName = e.target.tagName.toLowerCase();
    if (document.activeElement && (tagName === "input" || tagName === "select" || tagName === "textarea")) {
      document.activeElement.blur();
    } else {
      searxng.closeDetail();
    }
  }

  function pageButtonClick(css_selector) {
    return () => {
      const button = document.querySelector(css_selector);
      if (button) {
        button.click();
      }
    };
  }

  function GoToNextPage() {
    return pageButtonClick('nav#pagination .next_page button[type="submit"]');
  }

  function GoToPreviousPage() {
    return pageButtonClick('nav#pagination .previous_page button[type="submit"]');
  }

  function scrollPageToSelected() {
    const sel = document.querySelector(".result[data-vim-selected]");
    if (sel === null) {
      return;
    }
    const wtop = document.documentElement.scrollTop || document.body.scrollTop,
      wheight = document.documentElement.clientHeight,
      etop = sel.offsetTop,
      ebot = etop + sel.clientHeight,
      offset = 120;
    // first element ?
    if (sel.previousElementSibling === null && ebot < wheight) {
      // set to the top of page if the first element
      // is fully included in the viewport
      window.scroll(window.scrollX, 0);
      return;
    }
    if (wtop > etop - offset) {
      window.scroll(window.scrollX, etop - offset);
    } else {
      const wbot = wtop + wheight;
      if (wbot < ebot + offset) {
        window.scroll(window.scrollX, ebot - wheight + offset);
      }
    }
  }

  function scrollPage(amount) {
    return () => {
      window.scrollBy(0, amount);
      highlightResult("visible")();
    };
  }

  function scrollPageTo(position, nav) {
    return () => {
      window.scrollTo(0, position);
      highlightResult(nav)();
    };
  }

  function searchInputFocus() {
    window.scrollTo(0, 0);
    const q = document.querySelector("#q");
    q.focus();
    if (q.setSelectionRange) {
      const len = q.value.length;
      q.setSelectionRange(len, len);
    }
  }

  function openResult(newTab) {
    return () => {
      let link = document.querySelector(".result[data-vim-selected] h3 a");
      if (link === null) {
        link = document.querySelector(".result[data-vim-selected] > a");
      }
      if (link !== null) {
        const url = link.getAttribute("href");
        if (newTab) {
          window.open(url);
        } else {
          window.location.href = url;
        }
      }
    };
  }

  function initHelpContent(divElement) {
    const categories = {};

    for (const k in keyBindings) {
      const key = keyBindings[k];
      categories[key.cat] = categories[key.cat] || [];
      categories[key.cat].push(key);
    }

    const sorted = Object.keys(categories).sort((a, b) => categories[b].length - categories[a].length);

    if (sorted.length === 0) {
      return;
    }

    let html = '<a href="#" class="close" aria-label="close" title="close">×</a>';
    html += "<h3>How to navigate SearXNG with hotkeys</h3>";
    html += "<table>";

    for (let i = 0; i < sorted.length; i++) {
      const cat = categories[sorted[i]];

      const lastCategory = i === sorted.length - 1;
      const first = i % 2 === 0;

      if (first) {
        html += "<tr>";
      }
      html += "<td>";

      html += `<h4>${cat[0].cat}</h4>`;
      html += '<ul class="list-unstyled">';

      for (const cj in cat) {
        html += `<li><kbd>${cat[cj].key}</kbd> ${cat[cj].des}</li>`;
      }

      html += "</ul>";
      html += "</td>"; // col-sm-*

      if (!first || lastCategory) {
        html += "</tr>"; // row
      }
    }

    html += "</table>";

    divElement.innerHTML = html;
  }

  function toggleHelp() {
    let helpPanel = document.querySelector("#vim-hotkeys-help");
    if (helpPanel === undefined || helpPanel === null) {
      // first call
      helpPanel = document.createElement("div");
      helpPanel.id = "vim-hotkeys-help";
      helpPanel.className = "dialog-modal";
      initHelpContent(helpPanel);
      const body = document.getElementsByTagName("body")[0];
      body.appendChild(helpPanel);
    } else {
      // toggle hidden
      helpPanel.classList.toggle("invisible");
    }
  }

  function copyURLToClipboard() {
    const currentUrlElement = document.querySelector(".result[data-vim-selected] h3 a");
    if (currentUrlElement === null) return;

    const url = currentUrlElement.getAttribute("href");
    navigator.clipboard.writeText(url);
  }

  searxng.scrollPageToSelected = scrollPageToSelected;
  searxng.selectNext = highlightResult("down");
  searxng.selectPrevious = highlightResult("up");
});
