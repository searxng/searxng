import globals from "globals";
import pluginJs from "@eslint/js";


/** @type {import('eslint').Linter.Config[]} */
export default [
  pluginJs.configs.recommended,

  // global "ignores"
  // https://eslint.org/docs/latest/use/configure/configuration-files#globally-ignoring-files-with-ignores
  {
    ignores: ["node_modules/", "dist/"]
  },

  {
    files: [
      "**/*.js",
    ],
    linterOptions: {
      reportUnusedDisableDirectives: "error",
      // noInlineConfig: true
    },
    languageOptions: {
      sourceType: "module",
      globals: {
        ...globals.browser,
      }
    },
    rules: {
      indent: ["error", 2],
    },
  },

];
