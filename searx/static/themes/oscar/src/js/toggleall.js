/**
 * @license
 * (C) Copyright Contributors to the SearXNG project.
 * (C) Copyright Contributors to the searx project (2014 - 2021).
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

$(document).ready(function(){
    $("#allow-all-engines").click(function() {
        $(".onoffswitch-checkbox").each(function() { this.checked = false;});
    });

    $("#disable-all-engines").click(function() {
        $(".onoffswitch-checkbox").each(function() { this.checked = true;});
    });
});

