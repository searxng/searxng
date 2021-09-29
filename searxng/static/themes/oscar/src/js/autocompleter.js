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
    var original_search_value = '';
    if(searxng.autocompleter) {
        var searchResults = new Bloodhound({
            datumTokenizer: Bloodhound.tokenizers.obj.whitespace('value'),
            queryTokenizer: Bloodhound.tokenizers.whitespace,
            remote: {
                url: './autocompleter?q=%QUERY',
                wildcard: '%QUERY'
            }
        });
        searchResults.initialize();

        $("#q").on('keydown', function(e) {
			if(e.which == 13) {
                original_search_value = $('#q').val();
			}
		});
        $('#q').typeahead({
            name: 'search-results',
            highlight: false,
            hint: true,
            displayKey: function(result) {
                return result;
            },
            classNames: {
                input: 'tt-input',
                hint: 'tt-hint',
                menu: 'tt-dropdown-menu',
                dataset: 'tt-dataset-search-results',
            },
        }, {
            name: 'autocomplete',
            source: searchResults,
        });
        $('#q').bind('typeahead:select', function(ev, suggestion) {
            if(original_search_value) {
                $('#q').val(original_search_value);
            }
            $("#search_form").submit();
        });
    }
});
