/**
 * @license
 * SPDX-License-Identifier: AGPL-3.0-or-later
 *
 * svgo config: Optimize SVG for WEB usage
 */

module.exports = {
  plugins: [
    {
      name: 'preset-default',
    },
    // make diff friendly
    'sortAttrs',
 ],
};
