// SPDX-License-Identifier: AGPL-3.0-or-later

import { load } from "./loader.ts";
import { Endpoints, endpoint, listen, ready, settings } from "./toolkit.ts";

ready(() => {
  document.documentElement.classList.remove("no-js");
  document.documentElement.classList.add("js");

  listen("click", ".close", function (this: HTMLElement) {
    (this.parentNode as HTMLElement)?.classList.add("invisible");
  });

  listen("click", ".searxng_init_map", async function (this: HTMLElement, event: Event) {
    event.preventDefault();
    this.classList.remove("searxng_init_map");

    load(() => import("./plugin/MapView.ts").then(({ default: Plugin }) => new Plugin(this)), {
      on: "endpoint",
      where: [Endpoints.results]
    });
  });

  if (settings.plugins?.includes("infiniteScroll")) {
    load(() => import("./plugin/InfiniteScroll.ts").then(({ default: Plugin }) => new Plugin()), {
      on: "endpoint",
      where: [Endpoints.results]
    });
  }

  if (settings.plugins?.includes("calculator")) {
    load(() => import("./plugin/Calculator.ts").then(({ default: Plugin }) => new Plugin()), {
      on: "endpoint",
      where: [Endpoints.results]
    });
  }
});

ready(
  () => {
    void import("./main/keyboard.ts");
    void import("./main/search.ts");

    if (settings.autocomplete) {
      void import("./main/autocomplete.ts");
    }
  },
  { on: [endpoint === Endpoints.index] }
);

ready(
  () => {
    void import("./main/keyboard.ts");
    void import("./main/results.ts");
    void import("./main/search.ts");

    if (settings.autocomplete) {
      void import("./main/autocomplete.ts");
    }
  },
  { on: [endpoint === Endpoints.results] }
);

ready(
  () => {
    void import("./main/preferences.ts");
  },
  { on: [endpoint === Endpoints.preferences] }
);
