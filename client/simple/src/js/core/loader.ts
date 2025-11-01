// SPDX-License-Identifier: AGPL-3.0-or-later

import type { Plugin } from "./Plugin.ts";
import { type EndpointsKeys, endpoint } from "./toolkit.ts";

type Options = { on: "global" } | { on: "endpoint"; where: EndpointsKeys | EndpointsKeys[] };

export const load = async <T extends Plugin>(
  Plugin: () => Promise<{ default: new () => T }>,
  options: Options
): Promise<void> => {
  check(options).catch((why) => {
    console.debug("Load condition failed:", why);
  });

  new (await Plugin()).default();
};

const check = async (options: Options): Promise<void> => {
  switch (options.on) {
    case "global": {
      return;
    }
    case "endpoint": {
      if (
        (typeof options.where === "string" && options.where !== endpoint) ||
        (Array.isArray(options.where) && !options.where.includes(endpoint))
      ) {
        throw new Error("not on the expected endpoint");
      }

      return;
    }
    default:
      throw new Error(`unhandled "on" trigger`);
  }
};
