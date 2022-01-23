/**
 * @license
 * (C) Copyright Contributors to the SearXNG project.
 * (C) Copyright Contributors to the searx project (2014 - 2021).
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

$(document).ready(function() {
    function hasScrollbar() {
        var root = document.compatMode=='BackCompat'? document.body : document.documentElement;
        return root.scrollHeight>root.clientHeight;
    }

    function loadNextPage() {
        var formData = $('#pagination form:last').serialize();
        if (formData) {
            $('#pagination').html('<div class="loading-spinner"></div>');
            $.ajax({
                type: "POST",
                url: $('#search_form').prop('action'),
                data: formData,
                dataType: 'html',
                success: function(data) {
                    var body = $(data);
                    $('#pagination').remove();
                    $('#main_results').append('<hr/>');
                    $('#main_results').append(body.find('.result'));
                    $('#main_results').append(body.find('#pagination'));
                    if(!hasScrollbar()) {
                        loadNextPage();
                    }
                }
            });
        }
    }

    if (searxng.infinite_scroll) {
        var win = $(window);
        $("html").addClass('infinite_scroll');
        if(!hasScrollbar()) {
            loadNextPage();
        }
        win.on('scroll', function() {
            if ($(document).height() - win.height() - win.scrollTop() < 150) {
                loadNextPage();
            }
        });
    }

});
