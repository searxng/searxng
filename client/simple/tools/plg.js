/**
 * Custom vite plugins to build the web-client components of the simple theme.
 *
 * HINT:
 *
 *   This is an inital implementation for the migration of the build process
 *   from grunt to vite.  For fully support (vite: build & serve) more work is
 *   needed.
 */

import { svg2png } from "./img.js";
import { svg2svg } from "./img.js";

/**
 * Vite plugin to convert a list of SVG files to PNG.
 *
 * @param {import('./img.js').Src2Dest} items - Array of SVG files (src: SVG, dest:PNG) to convert.
 */
function plg_svg2png(items) {
  return {
    name: 'searxng-simple-svg2png',
    apply: 'build', // or 'serve'
    async writeBundle() { svg2png(items); },
  };
}

/**
 * Vite plugin to optimize SVG images for WEB.
 *
 * @param {import('svgo').Config} svgo_opts - Options passed to svgo.
 * @param {import('./img.js').Src2Dest} items - Array of SVG files (src:SVG, dest:SVG) to optimize.
 */
function plg_svg2svg(svgo_opts, items) {
  return {
    name: 'searxng-simple-svg2png',
    apply: 'build', // or 'serve'
    async writeBundle() { svg2svg(items, svgo_opts); },
  };
}

export { plg_svg2png, plg_svg2svg };
