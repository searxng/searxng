// SPDX-License-Identifier: AGPL-3.0-or-later

import { listen } from "../toolkit.ts";
import { getElement } from "../util/getElement.ts";
import { getCookie } from "../util/cookies.ts";

const searchForm: HTMLFormElement = getElement<HTMLFormElement>("search");
const searchInput: HTMLInputElement = getElement<HTMLInputElement>("q");
const searchReset: HTMLButtonElement = getElement<HTMLButtonElement>("clear_search");

const isMobile: boolean = window.matchMedia("(max-width: 50em)").matches;
const isResultsPage: boolean = document.querySelector("main")?.id === "main_results";

const categoryButtons: HTMLButtonElement[] = Array.from(
  document.querySelectorAll<HTMLButtonElement>("#categories_container button.category")
);

// Results per page persistence
const resultsPerPageHidden = document.getElementById("results_per_page_hidden") as HTMLInputElement | null;
if (resultsPerPageHidden && !resultsPerPageHidden.value) {
  resultsPerPageHidden.value = getCookie("results_per_page") || "";
}

if (searchInput.value.length === 0) {
  searchReset.classList.add("empty");
}

// focus search input on large screens
if (!(isMobile || isResultsPage)) {
  searchInput.focus();
}

// On mobile, move cursor to the end of the input on focus
if (isMobile) {
  listen("focus", searchInput, () => {
    // Defer cursor move until the next frame to prevent a visual jump
    requestAnimationFrame(() => {
      const end = searchInput.value.length;
      searchInput.setSelectionRange(end, end);
      searchInput.scrollLeft = searchInput.scrollWidth;
    });
  });
}

listen("input", searchInput, () => {
  searchReset.classList.toggle("empty", searchInput.value.length === 0);
});

listen("click", searchReset, (event: MouseEvent) => {
  event.preventDefault();
  searchInput.value = "";
  searchInput.focus();
  searchReset.classList.add("empty");
});

for (const button of categoryButtons) {
  listen("click", button, (event: MouseEvent) => {
    // If we click any category, we should decide whether to keep results_per_page
    if (resultsPerPageHidden) {
      if (button.name !== "category_videos") {
        resultsPerPageHidden.value = "";
      } else {
        // If switching TO videos, make sure it's set from cookie if empty
        if (!resultsPerPageHidden.value) {
          resultsPerPageHidden.value = getCookie("results_per_page") || "";
        }
      }
    }

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

if (document.querySelector("div.search_filters")) {
  const safesearchElement = document.getElementById("safesearch");
  if (safesearchElement) {
    listen("change", safesearchElement, () => searchForm.submit());
  }

  const timeRangeElement = document.getElementById("time_range");
  if (timeRangeElement) {
    listen("change", timeRangeElement, () => searchForm.submit());
  }

  const languageElement = document.getElementById("language");
  if (languageElement) {
    listen("change", languageElement, () => searchForm.submit());
  }
}

// override searchForm submit event
listen("submit", searchForm, (event: Event) => {
  event.preventDefault();

  if (categoryButtons.length > 0) {
    const searchCategories = getElement<HTMLInputElement>("selected-categories");
    const selected = categoryButtons.filter((button) => button.classList.contains("selected"));
    
    // Final check on submission: if "videos" is not the ONLY selected category, 
    // maybe we want to clear it? User said "Videos -> General", so if we move away from videos:
    const hasVideos = selected.some(btn => btn.name === "category_videos");
    if (!hasVideos && resultsPerPageHidden) {
      resultsPerPageHidden.value = "";
    }

    searchCategories.value = selected
      .map((button) => button.name.replace("category_", ""))
      .join(",");
  }

  searchForm.submit();
});
