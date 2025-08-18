// SPDX-License-Identifier: AGPL-3.0-or-later

import { listen } from "./toolkit.ts";

listen("click", ".close", function (this: HTMLElement) {
  (this.parentNode as HTMLElement)?.classList.add("invisible");
});
