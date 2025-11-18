// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * Custom vite plugins to build the web-client components of the simple theme.
 *
 * HINT:
 *   This is an initial implementation for the migration of the build process
 *   from grunt to vite.  For fully support (vite: build & serve) more work is
 *   needed.
 */

import type { Config } from "svgo";
import type { Plugin } from "vite";
import { type Src2Dest, svg2png, svg2svg } from "./img.ts";

/**
 * Vite plugin to convert a list of SVG files to PNG.
 *
 * @param items - Array of SVG files (src: SVG, dest:PNG) to convert.
 */
export const plg_svg2png = (items: Src2Dest[]): Plugin => {
  return {
    name: "searxng-simple-svg2png",
    apply: "build",
    writeBundle: () => {
      svg2png(items);
    }
  };
};

/**
 * Vite plugin to optimize SVG images for WEB.
 *
 * @param items - Array of SVG files (src:SVG, dest:SVG) to optimize.
 * @param svgo_opts - Options passed to svgo.
 */
export const plg_svg2svg = (items: Src2Dest[], svgo_opts: Config): Plugin => {
  return {
    name: "searxng-simple-svg2svg",
    apply: "build",
    writeBundle: () => {
      svg2svg(items, svgo_opts);
    }
  };
};
