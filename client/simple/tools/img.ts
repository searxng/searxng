import fs from "node:fs";
import path from "node:path";
import sharp from "sharp";
import type { Config } from "svgo";
import { optimize as svgo } from "svgo";

// Mapping of src to dest
export type Src2Dest = {
  // Name of the source file.
  src: string;
  // Name of the destination file.
  dest: string;
};

/**
 * Convert a list of SVG files to PNG.
 *
 * @param items - Array of SVG files (src: SVG, dest:PNG) to convert.
 */
export const svg2png = async (items: Src2Dest[]) => {
  for (const item of items) {
    try {
      fs.mkdirSync(path.dirname(item.dest), { recursive: true });

      const info = await sharp(item.src)
        .png({
          force: true,
          compressionLevel: 9,
          palette: true
        })
        .toFile(item.dest);

      console.log(`[svg2png] created ${item.dest} -- bytes: ${info.size}, w:${info.width}px,  h:${info.height}px`);
    } catch (err) {
      console.error(`ERROR: ${item.dest} -- ${err}`);
      throw err;
    }
  }
};

/**
 * Optimize SVG images for WEB.
 *
 * @param items - Array of SVG files (src:SVG, dest:SVG) to optimize.
 * @param svgo_opts - Options passed to svgo.
 */
export const svg2svg = (items: Src2Dest[], svgo_opts: Config) => {
  for (const item of items) {
    try {
      fs.mkdirSync(path.dirname(item.dest), { recursive: true });

      const raw = fs.readFileSync(item.src, "utf8");
      const opt = svgo(raw, svgo_opts);

      fs.writeFileSync(item.dest, opt.data);
      console.log(`[svg2svg] optimized: ${item.dest} -- src: ${item.src}`);
    } catch (err) {
      console.error(`ERROR: optimize src: ${item.src} -- ${err}`);
      throw err;
    }
  }
};
