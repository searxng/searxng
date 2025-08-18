// SPDX-License-Identifier: AGPL-3.0-or-later

import { assertElement, listen, settings } from "../core/toolkit.ts";

const submitIfQuery = (qInput: HTMLInputElement): void => {
  if (qInput.value.length > 0) {
    const search = document.getElementById("search") as HTMLFormElement | null;
    search?.submit();
  }
};

const updateClearButton = (qInput: HTMLInputElement, cs: HTMLElement): void => {
  cs.classList.toggle("empty", qInput.value.length === 0);
};

const createClearButton = (qInput: HTMLInputElement): void => {
  const cs = document.getElementById("clear_search");
  assertElement(cs);

  updateClearButton(qInput, cs);

  listen("click", cs, (event: MouseEvent) => {
    event.preventDefault();
    qInput.value = "";
    qInput.focus();
    updateClearButton(qInput, cs);
  });

  listen("input", qInput, () => updateClearButton(qInput, cs), { passive: true });
};

const qInput = document.getElementById("q") as HTMLInputElement | null;
assertElement(qInput);

const isMobile: boolean = window.matchMedia("(max-width: 50em)").matches;
const isResultsPage: boolean = document.querySelector("main")?.id === "main_results";

// focus search input on large screens
if (!(isMobile || isResultsPage)) {
  qInput.focus();
}

createClearButton(qInput);

// Additionally to searching when selecting a new category, we also
// automatically start a new search request when the user changes a search
// filter (safesearch, time range or language) (this requires JavaScript
// though)
if (
  settings.search_on_category_select &&
  // If .search_filters is undefined (invisible) we are on the homepage and
  // hence don't have to set any listeners
  document.querySelector(".search_filters")
) {
  const safesearchElement = document.getElementById("safesearch");
  if (safesearchElement) {
    listen("change", safesearchElement, () => submitIfQuery(qInput));
  }

  const timeRangeElement = document.getElementById("time_range");
  if (timeRangeElement) {
    listen("change", timeRangeElement, () => submitIfQuery(qInput));
  }

  const languageElement = document.getElementById("language");
  if (languageElement) {
    listen("change", languageElement, () => submitIfQuery(qInput));
  }
}

const categoryButtons: HTMLButtonElement[] = [
  ...document.querySelectorAll<HTMLButtonElement>("button.category_button")
];
for (const button of categoryButtons) {
  listen("click", button, (event: MouseEvent) => {
    if (event.shiftKey) {
      event.preventDefault();
      button.classList.toggle("selected");
      return;
    }

    // deselect all other categories
    for (const categoryButton of categoryButtons) {
      categoryButton.classList.toggle("selected", categoryButton === button);
    }
  });
}

const form: HTMLFormElement | null = document.querySelector<HTMLFormElement>("#search");
assertElement(form);

// override form submit action to update the actually selected categories
listen("submit", form, (event: Event) => {
  event.preventDefault();

  const categoryValuesInput = document.querySelector<HTMLInputElement>("#selected-categories");
  if (categoryValuesInput) {
    const categoryValues = categoryButtons
      .filter((button) => button.classList.contains("selected"))
      .map((button) => button.name.replace("category_", ""));

    categoryValuesInput.value = categoryValues.join(",");
  }

  form.submit();
});
