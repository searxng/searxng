// SPDX-License-Identifier: AGPL-3.0-or-later

import { ready } from "./toolkit.ts";

ready(() => {
  document.documentElement.classList.remove("no-js");
  document.documentElement.classList.add("js");
});
