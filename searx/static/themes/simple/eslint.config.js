module.exports = [
  {
    "rules": {
      "indent": ["error", 2],
      "keyword-spacing": ["error", { "before": true, "after": true }],
      "no-trailing-spaces": 2,
      "space-before-function-paren": ["error", "always"],
      "space-infix-ops": "error",
      "comma-spacing": ["error", { "before": false, "after": true }],
      "brace-style": ["error", "1tbs", { "allowSingleLine": true }],
      "curly": ["error", "multi-line"],
      "block-spacing": ["error", "always"],
      "dot-location": ["error", "property"],
      "key-spacing": ["error", { "beforeColon": false, "afterColon": true }],
      "spaced-comment": [
	"error", "always", {
          "line": { "markers": ["*package", "!", "/", ",", "="] },
          "block": { "balanced": true, "markers": ["*package", "!", ",", ":", "::", "flow-include"], "exceptions": ["*"] }
	}
      ]
    },
    languageOptions: {
      ecmaVersion: 12
    }
  }
];
