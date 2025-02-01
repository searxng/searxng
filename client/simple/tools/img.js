import fs from "fs";
import path from "path";
import sharp from "sharp";
import { optimize as svgo } from "svgo";

/**
 * @typedef {object} Src2Dest - Mapping of src to dest
 * @property {string} src - Name of the source file.
 * @property {string} dest - Name of the destination file.
 */


/**
 * Convert a list of SVG files to PNG.
 *
 * @param {Src2Dest[]} items - Array of SVG files (src: SVG, dest:PNG) to convert.
 */

async function svg2png (items) {
  items.forEach(
    async (item) => {
      try {
        fs.mkdir(path.dirname(item.dest), { recursive: true }, (err) => {
          if (err)
            throw err;
        });

        const info = await sharp(item.src).png({
          force: true,
          compressionLevel: 9,
          palette: true,
        }).toFile(item.dest);

        console.log(
          `[svg2png] created ${item.dest} -- bytes: ${info.size}, w:${info.width}px,  h:${info.height}px`
        );
      } catch (err) {
        console.error(`ERROR: ${item.dest} -- ${err}`);
        throw(err);
      }
    }
  );
}


/**
 * Optimize SVG images for WEB.
 *
 * @param {import('svgo').Config} svgo_opts - Options passed to svgo.
 * @param {Src2Dest[]} items - Array of SVG files (src:SVG, dest:SVG) to optimize.
 */

async function svg2svg(svgo_opts, items) {
  items.forEach(
    async (item) => {
      try {
        fs.mkdir(path.dirname(item.dest), { recursive: true }, (err) => {
          if (err)
            throw err;
        });

        const raw = fs.readFileSync(item.src, "utf8");
        const opt = svgo(raw, svgo_opts);
        fs.writeFileSync(item.dest, opt.data);
        console.log(
          `[svg2svg] optimized: ${item.dest} -- src: ${item.src}`
        );

      } catch (err) {
        console.error(`ERROR: optimize src: ${item.src} -- ${err}`);
        throw(err);
      }
    }
  );
}


export { svg2png, svg2svg };
