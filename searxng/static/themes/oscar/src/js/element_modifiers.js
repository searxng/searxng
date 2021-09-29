/**
 * searxng is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * searxng is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with searxng. If not, see < http://www.gnu.org/licenses/ >.
 *
 * (C) 2014 by Thomas Pointhuber, <thomas.pointhuber@gmx.at>
 */

$(document).ready(function(){
    /**
     * focus element if class="autofocus" and id="q"
     */
    $('#q.autofocus').focus();

    /**
     * Empty search bar when click on reset button
     */
    $("#clear_search").click(function () {
	document.getElementById("q").value = "";
    });

    /**
     * select full content on click if class="select-all-on-click"
     */
    $(".select-all-on-click").click(function () {
        $(this).select();
    });

    /**
     * change text during btn-collapse click if possible
     */
    $('.btn-collapse').click(function() {
        var btnTextCollapsed = $(this).data('btn-text-collapsed');
        var btnTextNotCollapsed = $(this).data('btn-text-not-collapsed');

        if(btnTextCollapsed !== '' && btnTextNotCollapsed !== '') {
            if($(this).hasClass('collapsed')) {
                new_html = $(this).html().replace(btnTextCollapsed, btnTextNotCollapsed);
            } else {
                new_html = $(this).html().replace(btnTextNotCollapsed, btnTextCollapsed);
            }
            $(this).html(new_html);
        }
    });

    /**
     * change text during btn-toggle click if possible
     */
    $('.btn-toggle .btn').click(function() {
        var btnClass = 'btn-' + $(this).data('btn-class');
        var btnLabelDefault = $(this).data('btn-label-default');
        var btnLabelToggled = $(this).data('btn-label-toggled');
        if(btnLabelToggled !== '') {
            if($(this).hasClass('btn-default')) {
                new_html = $(this).html().replace(btnLabelDefault, btnLabelToggled);
            } else {
                new_html = $(this).html().replace(btnLabelToggled, btnLabelDefault);
            }
            $(this).html(new_html);
        }
        $(this).toggleClass(btnClass);
        $(this).toggleClass('btn-default');
    });

        /**
     * change text during btn-toggle click if possible
     */
    $('.media-loader').click(function() {
        var target = $(this).data('target');
        var iframe_load = $(target + ' > iframe');
        var srctest = iframe_load.attr('src');
        if(srctest === undefined || srctest === false){
            iframe_load.attr('src', iframe_load.data('src'));
        }
    });

    /**
     * Select or deselect every categories on double clic
     */
    $(".btn-sm").dblclick(function() {
    var btnClass = 'btn-' + $(this).data('btn-class'); // primary
        if($(this).hasClass('btn-default')) {
            $(".btn-sm > input").attr('checked', 'checked');
            $(".btn-sm > input").prop("checked", true);
            $(".btn-sm").addClass(btnClass);
            $(".btn-sm").addClass('active');
            $(".btn-sm").removeClass('btn-default');
        } else {
            $(".btn-sm > input").attr('checked', '');
            $(".btn-sm > input").removeAttr('checked');
            $(".btn-sm > input").checked = false;
            $(".btn-sm").removeClass(btnClass);
            $(".btn-sm").removeClass('active');
            $(".btn-sm").addClass('btn-default');
        }
    });
    $(".nav-tabs").click(function(a) {
        var tabs = $(a.target).parents("ul");
        tabs.children().attr("aria-selected", "false");
        $(a.target).parent().attr("aria-selected", "true");
    });

    /**
     * Layout images according to their sizes
     */
    searxng.image_thumbnail_layout = new searxng.ImageLayout('#main_results', '#main_results .result-images', 'img.img-thumbnail', 15, 200);
    searxng.image_thumbnail_layout.watch();
});
