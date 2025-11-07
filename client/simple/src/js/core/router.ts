// SPDX-License-Identifier: AGPL-3.0-or-later

import { Endpoints, endpoint, ready, settings } from "./toolkit.ts";

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

    if (settings.infinite_scroll) {
      void import("../main/infinite_scroll.ts");
    }

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
