// SPDX-License-Identifier: AGPL-3.0-or-later

import { listen, mutable, settings } from "../toolkit.ts";
import { assertElement } from "../util/assertElement.ts";

export type KeyBindingLayout = "default" | "vim";

type KeyBinding = {
  key: string;
  fun: (event: KeyboardEvent) => void;
  des: string;
  cat: string;
};

type HighlightResultElement = "down" | "up" | "visible" | "bottom" | "top";

/* common base for layouts */
const baseKeyBinding: Record<string, KeyBinding> = {
  Escape: {
    key: "ESC",
    fun: (event: KeyboardEvent) => removeFocus(event),
    des: "remove focus from the focused input",
    cat: "Control"
  },
  c: {
    key: "c",
    fun: () => copyURLToClipboard(),
    des: "copy url of the selected result to the clipboard",
    cat: "Results"
  },
  h: {
    key: "h",
    fun: () => toggleHelp(keyBindings),
    des: "toggle help window",
    cat: "Other"
  },
  i: {
    key: "i",
    fun: () => searchInputFocus(),
    des: "focus on the search input",
    cat: "Control"
  },
  n: {
    key: "n",
    fun: () => GoToNextPage(),
    des: "go to next page",
    cat: "Results"
  },
  o: {
    key: "o",
    fun: () => openResult(false),
    des: "open search result",
    cat: "Results"
  },
  p: {
    key: "p",
    fun: () => GoToPreviousPage(),
    des: "go to previous page",
    cat: "Results"
  },
  r: {
    key: "r",
    fun: () => reloadPage(),
    des: "reload page from the server",
    cat: "Control"
  },
  t: {
    key: "t",
    fun: () => openResult(true),
    des: "open the result in a new tab",
    cat: "Results"
  }
};

const keyBindingLayouts: Record<KeyBindingLayout, Record<string, KeyBinding>> = {
  // SearXNG layout
  default: {
    ArrowLeft: {
      key: "←",
      fun: () => highlightResult("up")(),
      des: "select previous search result",
      cat: "Results"
    },
    ArrowRight: {
      key: "→",
      fun: () => highlightResult("down")(),
      des: "select next search result",
      cat: "Results"
    },
    ...baseKeyBinding
  },

  // Vim-like keyboard layout
  vim: {
    b: {
      key: "b",
      fun: () => scrollPage(-window.innerHeight),
      des: "scroll one page up",
      cat: "Navigation"
    },
    d: {
      key: "d",
      fun: () => scrollPage(window.innerHeight / 2),
      des: "scroll half a page down",
      cat: "Navigation"
    },
    f: {
      key: "f",
      fun: () => scrollPage(window.innerHeight),
      des: "scroll one page down",
      cat: "Navigation"
    },
    g: {
      key: "g",
      fun: () => scrollPageTo(-document.body.scrollHeight, "top"),
      des: "scroll to the top of the page",
      cat: "Navigation"
    },
    j: {
      key: "j",
      fun: () => highlightResult("down")(),
      des: "select next search result",
      cat: "Results"
    },
    k: {
      key: "k",
      fun: () => highlightResult("up")(),
      des: "select previous search result",
      cat: "Results"
    },
    u: {
      key: "u",
      fun: () => scrollPage(-window.innerHeight / 2),
      des: "scroll half a page up",
      cat: "Navigation"
    },
    v: {
      key: "v",
      fun: () => scrollPageTo(document.body.scrollHeight, "bottom"),
      des: "scroll to the bottom of the page",
      cat: "Navigation"
    },
    y: {
      key: "y",
      fun: () => copyURLToClipboard(),
      des: "copy url of the selected result to the clipboard",
      cat: "Results"
    },
    ...baseKeyBinding
  }
};

const keyBindings: Record<string, KeyBinding> =
  settings.hotkeys && settings.hotkeys in keyBindingLayouts
    ? keyBindingLayouts[settings.hotkeys]
    : keyBindingLayouts.default;

const isElementInDetail = (element?: HTMLElement): boolean => {
  const ancestor = element?.closest(".detail, .result");
  return ancestor?.classList.contains("detail") ?? false;
};

const getResultElement = (element?: HTMLElement): HTMLElement | undefined => {
  return element?.closest(".result") ?? undefined;
};

const isImageResult = (resultElement?: HTMLElement): boolean => {
  return resultElement?.classList.contains("result-images") ?? false;
};

const highlightResult =
  (which: HighlightResultElement | HTMLElement) =>
  (noScroll?: boolean, keepFocus?: boolean): void => {
    let effectiveWhich = which;
    let current = document.querySelector<HTMLElement>(".result[data-vim-selected]");
    if (!current) {
      // no selection : choose the first one
      current = document.querySelector<HTMLElement>(".result");
      if (!current) {
        // no first one : there are no results
        return;
      }
      // replace up/down actions by selecting first one
      if (which === "down" || which === "up") {
        effectiveWhich = current;
      }
    }

    const results = Array.from(document.querySelectorAll<HTMLElement>(".result"));

    let next: HTMLElement | undefined;

    if (typeof effectiveWhich !== "string") {
      next = effectiveWhich;
    } else {
      switch (effectiveWhich) {
        case "visible": {
          const top = document.documentElement.scrollTop || document.body.scrollTop;
          const bot = top + document.documentElement.clientHeight;

          for (const element of results) {
            const etop = element.offsetTop;
            const ebot = etop + element.clientHeight;
            if (ebot <= bot && etop > top) {
              next = element;
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
          next = results.at(-1);
          break;
        // biome-ignore lint/complexity/noUselessSwitchCase: fallthrough is intended
        case "top":
        default:
          [next] = results;
      }
    }

    if (next) {
      current.removeAttribute("data-vim-selected");
      next.setAttribute("data-vim-selected", "true");

      if (!keepFocus) {
        const link = next.querySelector<HTMLAnchorElement>("h3 a") || next.querySelector<HTMLAnchorElement>("a");
        link?.focus();
      }

      if (!noScroll) {
        mutable.scrollPageToSelected?.();
      }
    }
  };

const reloadPage = (): void => {
  document.location.reload();
};

const removeFocus = (event: KeyboardEvent): void => {
  const target = event.target as HTMLElement;
  const tagName = target?.tagName?.toLowerCase();

  if (document.activeElement && (tagName === "input" || tagName === "select" || tagName === "textarea")) {
    (document.activeElement as HTMLElement).blur();
  } else {
    mutable.closeDetail?.();
  }
};

const pageButtonClick = (css_selector: string): void => {
  const button = document.querySelector<HTMLButtonElement>(css_selector);
  if (button) {
    button.click();
  }
};

const GoToNextPage = (): void => {
  pageButtonClick('nav#pagination .next_page button[type="submit"]');
};

const GoToPreviousPage = (): void => {
  pageButtonClick('nav#pagination .previous_page button[type="submit"]');
};

mutable.scrollPageToSelected = (): void => {
  const sel = document.querySelector<HTMLElement>(".result[data-vim-selected]");
  if (!sel) return;

  const wtop = document.documentElement.scrollTop || document.body.scrollTop;
  const height = document.documentElement.clientHeight;
  const etop = sel.offsetTop;
  const ebot = etop + sel.clientHeight;
  const offset = 120;

  // first element ?
  if (!sel.previousElementSibling && ebot < height) {
    // set to the top of page if the first element
    // is fully included in the viewport
    window.scroll(window.scrollX, 0);
    return;
  }

  if (wtop > etop - offset) {
    window.scroll(window.scrollX, etop - offset);
  } else {
    const wbot = wtop + height;
    if (wbot < ebot + offset) {
      window.scroll(window.scrollX, ebot - height + offset);
    }
  }
};

const scrollPage = (amount: number): void => {
  window.scrollBy(0, amount);
  highlightResult("visible")();
};

const scrollPageTo = (position: number, nav: HighlightResultElement): void => {
  window.scrollTo(0, position);
  highlightResult(nav)();
};

const searchInputFocus = (): void => {
  window.scrollTo(0, 0);

  const q = document.querySelector<HTMLInputElement>("#q");
  if (q) {
    q.focus();

    if (q.setSelectionRange) {
      const len = q.value.length;

      q.setSelectionRange(len, len);
    }
  }
};

const openResult = (newTab: boolean): void => {
  let link = document.querySelector<HTMLAnchorElement>(".result[data-vim-selected] h3 a");
  if (!link) {
    link = document.querySelector<HTMLAnchorElement>(".result[data-vim-selected] > a");
  }
  if (!link) return;

  const url = link.getAttribute("href");
  if (url) {
    if (newTab) {
      window.open(url);
    } else {
      window.location.href = url;
    }
  }
};

const initHelpContent = (divElement: HTMLElement, keyBindings: typeof baseKeyBinding): void => {
  const categories: Record<string, KeyBinding[]> = {};

  for (const binding of Object.values(keyBindings)) {
    const { cat } = binding;
    categories[cat] ??= [];
    categories[cat].push(binding);
  }

  const sortedCategoryKeys = Object.keys(categories).sort(
    (a, b) => (categories[b]?.length ?? 0) - (categories[a]?.length ?? 0)
  );

  let html = '<a href="#" class="close" aria-label="close" title="close">×</a>';
  html += "<h3>How to navigate SearXNG with hotkeys</h3>";
  html += "<table>";

  for (const [i, categoryKey] of sortedCategoryKeys.entries()) {
    const bindings = categories[categoryKey];
    if (!bindings || bindings.length === 0) continue;

    const isFirst = i % 2 === 0;
    const isLast = i === sortedCategoryKeys.length - 1;

    if (isFirst) {
      html += "<tr>";
    }

    html += "<td>";
    html += `<h4>${categoryKey}</h4>`;
    html += '<ul class="list-unstyled">';

    for (const binding of bindings) {
      html += `<li><kbd>${binding.key}</kbd> ${binding.des}</li>`;
    }

    html += "</ul>";
    html += "</td>";

    if (!isFirst || isLast) {
      html += "</tr>";
    }
  }

  html += "</table>";

  divElement.innerHTML = html;
};

const toggleHelp = (keyBindings: typeof baseKeyBinding): void => {
  let helpPanel = document.querySelector<HTMLElement>("#vim-hotkeys-help");
  if (helpPanel) {
    // toggle hidden
    helpPanel.classList.toggle("invisible");
  } else {
    // first call
    helpPanel = Object.assign(document.createElement("div"), {
      id: "vim-hotkeys-help",
      className: "dialog-modal"
    });
    initHelpContent(helpPanel, keyBindings);
    const [body] = document.getElementsByTagName("body");
    if (body) {
      body.appendChild(helpPanel);
    }
  }
};

const copyURLToClipboard = async (): Promise<void> => {
  const selectedResult = document.querySelector<HTMLElement>(".result[data-vim-selected]");
  if (!selectedResult) return;

  const resultAnchor = selectedResult.querySelector<HTMLAnchorElement>("a");
  assertElement(resultAnchor);

  const url = resultAnchor.getAttribute("href");
  if (url) {
    if (window.isSecureContext) {
      await navigator.clipboard.writeText(url);
    } else {
      const selection = window.getSelection();
      if (selection) {
        const node = document.createElement("span");
        node.textContent = url;
        resultAnchor.appendChild(node);

        const range = document.createRange();
        range.selectNodeContents(node);
        selection.removeAllRanges();
        selection.addRange(range);
        document.execCommand("copy");
        node.remove();
      }
    }
  }
};

listen("click", ".result", function (this: HTMLElement, event: PointerEvent) {
  if (!isElementInDetail(event.target as HTMLElement)) {
    highlightResult(this)(true, true);

    const resultElement = getResultElement(event.target as HTMLElement);

    if (resultElement && isImageResult(resultElement)) {
      event.preventDefault();
      mutable.selectImage?.(resultElement);
    }
  }
});

// FIXME: Focus might also trigger Pointer event ^^^
listen(
  "focus",
  ".result a",
  (event: FocusEvent) => {
    if (!isElementInDetail(event.target as HTMLElement)) {
      const resultElement = getResultElement(event.target as HTMLElement);

      if (resultElement && !resultElement.hasAttribute("data-vim-selected")) {
        highlightResult(resultElement)(true);
      }

      if (resultElement && isImageResult(resultElement)) {
        event.preventDefault();
        mutable.selectImage?.(resultElement);
      }
    }
  },
  { capture: true }
);

listen("keydown", document, (event: KeyboardEvent) => {
  // check for modifiers so we don't break browser's hotkeys
  if (Object.hasOwn(keyBindings, event.key) && !event.ctrlKey && !event.altKey && !event.shiftKey && !event.metaKey) {
    const tagName = (event.target as HTMLElement)?.tagName?.toLowerCase();

    if (event.key === "Escape") {
      keyBindings[event.key]?.fun(event);
    } else if (event.target === document.body || tagName === "a" || tagName === "button") {
      event.preventDefault();
      keyBindings[event.key]?.fun(event);
    }
  }
});

mutable.selectNext = highlightResult("down");
mutable.selectPrevious = highlightResult("up");
