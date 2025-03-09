/**
 * CONFIG: https://vite.dev/config/
 */

import { resolve, relative } from "node:path";
import { Buffer } from 'buffer';
import path from 'path';
import { defineConfig } from "vite";
import stylelint from "vite-plugin-stylelint";
import { viteStaticCopy } from "vite-plugin-static-copy";
import { plg_svg2png } from "./tools/plg.js";
import { plg_svg2svg } from "./tools/plg.js";
import fs from 'node:fs/promises';
import crypto from 'node:crypto';


const ROOT = "../..";  // root of the git reposetory

const PATH = {

  dist: resolve(ROOT, "searx/static/themes/simple"),
  // dist: resolve(ROOT, "client/simple/dist"),

  src: "src",
  modules: "node_modules",
  brand: "src/brand",
  static: resolve(ROOT, "client/simple/static"),
  leaflet: resolve(ROOT, "client/simple/node_modules/leaflet/dist"),
  templates: resolve(ROOT, "searx/templates/simple"),
};

const svg2svg_opts = {
  plugins: [
    { name: "preset-default" },
    "sortAttrs",
    "convertStyleToAttrs",
  ]
};

const svg2svg_favicon_opts = {
  plugins: [
    { name: "preset-default" },
    "sortAttrs",
  ]
};

function AddSearxNGHashes(options = {}) {
  const {
    fileName = "hashes.json",
    exclude = [],
    include_without_hashes = []
  } = options;
  let outDir = null;

  // Helper: recursively get all files (not directories) within `dir`.
  async function getAllFiles(dir) {
    let entries = await fs.readdir(dir, { withFileTypes: true });
    let files = [];
    for (const entry of entries) {
      const fullPath = resolve(dir, entry.name);
      if (entry.isDirectory()) {
        files = files.concat(await getAllFiles(fullPath));
      } else {
        files.push(fullPath);
      }
    }

    // Separate out `.map` files so they end up last
    const mapFiles = files.filter((file) => file.endsWith(".map"));
    const otherFiles = files.filter((file) => !file.endsWith(".map"));
  
    return [...otherFiles, ...mapFiles];
  }

  function replacePathsInBuffer(body, mapping) {
    // Convert the Buffer to a string (assuming UTF-8)
    let content = body.toString("utf-8");
  
    // Perform replacements
    for (const logicalPath of Object.keys(mapping)) {
      const hashedPath = mapping[logicalPath];
      content = content.replaceAll(logicalPath, hashedPath);
    }
  
    // Convert the modified string back to a Buffer
    return Buffer.from(content, "utf-8");
  }

  return {
    name: "recursive-hash-manifest-plugin",
    apply: "build",

    // Capture the final "outDir" from the resolved Vite config
    configResolved(config) {
      outDir = config.build.outDir;
    },

    // "closeBundle" is called after everything (including other async tasks) is done writing
    async closeBundle() {
      // Check if the outDir is set (from configResolved)
      if (outDir === null) {
        return
      }

      // Get a list of every file in the output directory
      let allFiles = await getAllFiles(outDir);

      // Optionally exclude certain files
      const exclusionSet = new Set([...exclude, fileName]);
      allFiles = allFiles.filter((filePath) => {
        const relPath = relative(outDir, filePath);
        return !exclusionSet.has(relPath);
      });

      // Compute a hash for each file
      const assets = {};
      const var_mapping = {}
      const hash_override = {}
      for (const filePath of allFiles) {
        const relPath = relative(outDir, filePath);

        // Get the shortHash
        let shortHash;

        if (include_without_hashes.includes(relative(outDir, filePath))) {
          shortHash = "";
        } else if (Object.prototype.hasOwnProperty.call(hash_override, filePath)) {
          shortHash = hash_override[filePath];
        } else {
          const fileBuf = await fs.readFile(filePath);
          const hashSum = crypto.createHash("sha256").update(fileBuf).digest("hex");
          shortHash = "." + hashSum.slice(0, 8);
          hash_override[filePath + ".map"] = shortHash;  
        }

        // Prepare to build a new file path
        const dirName = path.dirname(filePath);
        let newFilePath;
        let varPath = null;

        // Special handling for *.js.map
        if (filePath.endsWith(".js.map")) {
          const baseName = path.basename(filePath, ".js.map"); 
          newFilePath = path.join(dirName, `${baseName}${shortHash}.js.map`);
        }
        // Special handling for *.css.map
        else if (filePath.endsWith(".css.map")) {
          const baseName = path.basename(filePath, ".css.map");
          newFilePath = path.join(dirName, `${baseName}${shortHash}.css.map`);
        } 
        // Otherwise, rename as usual
        else {
          const extName = path.extname(filePath);
          const baseName = path.basename(filePath, extName);
          newFilePath = path.join(dirName, `${baseName}${shortHash}${extName}`);

          //
          varPath = `${baseName}.SEARXNG_HASH${extName}`;
          var_mapping[varPath] = `${baseName}${shortHash}${extName}`;
          if (filePath.endsWith(".js")) {
            var_mapping[`//# sourceMappingURL=${baseName}${extName}.map`] = `//# sourceMappingURL=${baseName}${shortHash}${extName}.map`;
          }
        }

        // New relative path
        const newRelPath = relative(outDir, newFilePath);
        assets[relPath] = newRelPath;
      }

      // Step 2: Once the manifest is all set, read back files that might reference others
      //         and replace placeholders with hashed paths.
      for (const filePath of allFiles) {
        const extName = path.extname(filePath);
        if (![".css", ".js", ".html"].includes(extName)) {
          continue;
        }
        const originalBuf = await fs.readFile(filePath);
        const replacedBuf = replacePathsInBuffer(originalBuf, var_mapping);
        await fs.writeFile(filePath, replacedBuf);
      }

      // Step 3: rename the original files to their hashed filenames
      for (const filePath of allFiles) {
        const relPath = path.relative(outDir, filePath);
        const newRelPath = assets[relPath];
        const newFilePath = path.join(outDir, newRelPath);
        await fs.rename(filePath, newFilePath);
      }

      // Write out `assets.json`
      const assetsPath = resolve(outDir, fileName);
      await fs.writeFile(assetsPath, JSON.stringify(assets, null, 2), "utf-8");
    },
  };
}

export default defineConfig({

  root: PATH.src,
  mode: "production",
  // mode: "development",

  // FIXME: missing CCS sourcemaps!!
  // see: https://github.com/vitejs/vite/discussions/13845#discussioncomment-11992084
  //
  // what I have tried so far (see config below):
  //
  // - build.sourcemap
  // - esbuild.sourcemap
  // - css.preprocessorOptions.less.sourceMap

  css: {
    devSourcemap: true,
    preprocessorOptions: {
      less: {
        // FIXME: missing CCS sourcemaps!!
        sourceMap: {
          outputSourceFiles: true,
          sourceMapURL: (name) => { const s = name.split('/'); return s[s.length - 1] + '.map'; },
        },
        // env: 'development',
        // relativeUrls: true,
        // javascriptEnabled: true,
      },
    },
  },  // end: css

  esbuild : {
    // FIXME: missing CCS sourcemaps!!
    sourcemap: true
  },

  build: {
    manifest: "manifest.json",
    emptyOutDir: true,
    assetsDir: "",
    outDir: PATH.dist,

    // FIXME: missing CCS sourcemaps!!
    sourcemap: true,

    // https://vite.dev/config/build-options.html#build-cssminify
    cssMinify: true,
    // cssMinify: "esbuild",
    minify: "esbuild",

    rollupOptions: {
      input: {

        // build CSS files
        "css/searxng.min.css": PATH.src + "/less/style-ltr.less",
        "css/searxng-rtl.min.css": PATH.src + "/less/style-rtl.less",
        "css/rss.min.css": PATH.src + "/less/rss.less",

        // build JS files
        "js/searxng.head.min": PATH.src + "/js/searxng.head.js",
        "js/searxng.min": PATH.src + "/js/searxng.js",

      },

      // file naming conventions / pathnames are relative to outDir (PATH.dist)
      output: {
        entryFileNames: "[name].js",
        chunkFileNames: "[name].js",
        assetFileNames: "[name].[ext]",
        // Vite does not support "rollupOptions.output.sourcemap".
        // Please use "build.sourcemap" instead.
        // sourcemap: true,
      },

    },
  },  // end: build

  plugins: [

    stylelint({
      build: true,
      emitWarningAsError: true,
      fix: true,
    }),

    // Leaflet

    viteStaticCopy({
      targets: [
        { src: PATH.leaflet + "/leaflet.{js,js.map}", dest: PATH.dist + "/js" },
        { src: PATH.leaflet + "/images/*.png", dest: PATH.dist + "/css/images/" },
        { src: PATH.leaflet + "/*.{css,css.map}", dest: PATH.dist + "/css" },
        { src: PATH.static + "/**/*", dest: PATH.dist },
      ]
    }),

    // -- svg images

    plg_svg2svg(
      [
        { src: PATH.src + "/svg/empty_favicon.svg", dest: PATH.dist + "/img/empty_favicon.svg" },
        { src: PATH.src + "/svg/select-dark.svg", dest: PATH.dist + "/img/select-dark.svg" },
        { src: PATH.src + "/svg/select-light.svg", dest: PATH.dist + "/img/select-light.svg" },
      ],
      svg2svg_opts,
    ),

    // SearXNG brand (static)

    plg_svg2png(
      [
        { src: PATH.brand + "/searxng-wordmark.svg", dest: PATH.dist + "/img/favicon.png" },
        { src: PATH.brand + "/searxng.svg", dest: PATH.dist + "/img/searxng.png" },
      ],
    ),

    // -- svg
    plg_svg2svg(
      [
        { src: PATH.brand + "/searxng.svg", dest: PATH.dist + "/img/searxng.svg" },
        { src: PATH.brand + "/img_load_error.svg", dest: PATH.dist + "/img/img_load_error.svg" },
      ],
      svg2svg_opts,
    ),

    // -- favicon
    plg_svg2svg(
      [ { src: PATH.brand + "/searxng-wordmark.svg", dest: PATH.dist + "/img/favicon.svg" } ],
      svg2svg_favicon_opts,
    ),

    // -- simple templates
    plg_svg2svg(
      [
        { src: PATH.brand + "/searxng-wordmark.svg", dest: PATH.templates + "/searxng-wordmark.min.svg" },
      ],
      svg2svg_opts
    ),

    // -- create assets.json and add hashes to files
    AddSearxNGHashes({
      fileName: "assets.json",
      exclude: [
        ".gitattributes",
        "manifest.json"
      ],
      include_without_hashes: [
        "css/images/layers-2x.png",
        "css/images/layers.png",
        "css/images/marker-icon-2x.png",
        "css/images/marker-icon.png",
        "css/images/marker-shadow.png",
      ]
    }),

  ] // end: plugins

});
