// SPDX-License-Identifier: AGPL-3.0-or-later

import type { Plugin } from "./Plugin.ts";
import { type EndpointsKeys, endpoint } from "./toolkit.ts";

type Options =
  | {
      on: "global";
    }
  | {
      on: "endpoint";
      where: EndpointsKeys[];
    };

export const load = <T extends Plugin>(instance: () => Promise<T>, options: Options): void => {
  if (!check(options)) return;

  void instance();
};

const check = (options: Options): boolean => {
  switch (options.on) {
    case "global": {
      return true;
    }
    case "endpoint": {
      if (!options.where.includes(endpoint)) {
        // not on the expected endpoint
        return false;
      }

      return true;
    }
    default: {
      return false;
    }
  }
};
