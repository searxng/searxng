import globals from "globals";
import path from "node:path";
import { fileURLToPath } from "node:url";
import js from "@eslint/js";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const compat = new FlatCompat({
    baseDirectory: __dirname,
    recommendedConfig: js.configs.recommended,
    allConfig: js.configs.all
});

export default [...compat.extends("eslint:recommended"), {
    languageOptions: {
        globals: {
            ...globals.browser,
            ...globals.node,
        },

        ecmaVersion: 12,
        sourceType: "commonjs",
    },

    rules: {
        indent: ["error", 2],

        "keyword-spacing": ["error", {
            before: true,
            after: true,
        }],

        "no-trailing-spaces": 2,
        "space-before-function-paren": ["error", "always"],
        "space-infix-ops": "error",

        "comma-spacing": ["error", {
            before: false,
            after: true,
        }],

        "brace-style": ["error", "1tbs", {
            allowSingleLine: true,
        }],

        curly: ["error", "multi-line"],
        "block-spacing": ["error", "always"],
        "dot-location": ["error", "property"],

        "key-spacing": ["error", {
            beforeColon: false,
            afterColon: true,
        }],

        "spaced-comment": ["error", "always", {
            line: {
                markers: ["*package", "!", "/", ",", "="],
            },

            block: {
                balanced: true,
                markers: ["*package", "!", ",", ":", "::", "flow-include"],
                exceptions: ["*"],
            },
        }],
    },
}];