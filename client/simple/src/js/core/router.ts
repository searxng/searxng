// SPDX-License-Identifier: AGPL-3.0-or-later

import { Endpoints, endpoint, ready, settings } from "./toolkit.ts";

ready(
  () => {
    import("../main/keyboard.ts");
    import("../main/search.ts");

    if (settings.autocomplete) {
      import("../main/autocomplete.ts");
    }
  },
  { on: [endpoint === Endpoints.index] }
);

ready(
  () => {
    import("../main/keyboard.ts");
    import("../main/mapresult.ts");
    import("../main/results.ts");
    import("../main/search.ts");

    if (settings.infinite_scroll) {
      import("../main/infinite_scroll.ts");
    }

    if (settings.autocomplete) {
      import("../main/autocomplete.ts");
    }
  },
  { on: [endpoint === Endpoints.results] }
);

ready(
  () => {
    import("../main/preferences.ts");
  },
  { on: [endpoint === Endpoints.preferences] }
);
