// SPDX-License-Identifier: AGPL-3.0-or-later

import { load } from "./loader.ts";
import { Endpoints, endpoint, ready, settings } from "./toolkit.ts";

ready(() => {
  document.documentElement.classList.remove("no-js");
  document.documentElement.classList.add("js");

  void load(() => import("../plugin/QueryPlugin.ts"), {
    on: "endpoint",
    where: Endpoints.results
  });

  if (settings.infinite_scroll) {
    void load(() => import("../plugin/InfiniteScrollPlugin.ts"), {
      on: "endpoint",
      where: Endpoints.results
    });
  }
});

ready(
  () => {
    void import("../main/keyboard.ts");
    void import("../main/search.ts");

    if (settings.autocomplete) {
      void import("../main/autocomplete.ts");
    }
  },
  { on: [endpoint === Endpoints.index] }
);

ready(
  () => {
    void import("../main/keyboard.ts");
    void import("../main/mapresult.ts");
    void import("../main/results.ts");
    void import("../main/search.ts");

    if (settings.autocomplete) {
      void import("../main/autocomplete.ts");
    }
  },
  { on: [endpoint === Endpoints.results] }
);

ready(
  () => {
    void import("../main/preferences.ts");
  },
  { on: [endpoint === Endpoints.preferences] }
);
