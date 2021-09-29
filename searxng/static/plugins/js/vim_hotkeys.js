$(document).ready(function() {
    highlightResult('top')();

    $('.result').on('click', function() {
        highlightResult($(this))();
    });

    var vimKeys = {
        27: {
            key: 'Escape',
            fun: removeFocus,
            des: 'remove focus from the focused input',
            cat: 'Control'
        },
        73: {
            key: 'i',
            fun: searchInputFocus,
            des: 'focus on the search input',
            cat: 'Control'
        },
        66: {
            key: 'b',
            fun: scrollPage(-window.innerHeight),
            des: 'scroll one page up',
            cat: 'Navigation'
        },
        70: {
            key: 'f',
            fun: scrollPage(window.innerHeight),
            des: 'scroll one page down',
            cat: 'Navigation'
        },
        85: {
            key: 'u',
            fun: scrollPage(-window.innerHeight / 2),
            des: 'scroll half a page up',
            cat: 'Navigation'
        },
        68: {
            key: 'd',
            fun: scrollPage(window.innerHeight / 2),
            des: 'scroll half a page down',
            cat: 'Navigation'
        },
        71: {
            key: 'g',
            fun: scrollPageTo(-document.body.scrollHeight, 'top'),
            des: 'scroll to the top of the page',
            cat: 'Navigation'
        },
        86: {
            key: 'v',
            fun: scrollPageTo(document.body.scrollHeight, 'bottom'),
            des: 'scroll to the bottom of the page',
            cat: 'Navigation'
        },
        75: {
            key: 'k',
            fun: highlightResult('up'),
            des: 'select previous search result',
            cat: 'Results'
        },
        74: {
            key: 'j',
            fun: highlightResult('down'),
            des: 'select next search result',
            cat: 'Results'
        },
        80: {
            key: 'p',
            fun: pageButtonClick(0),
            des: 'go to previous page',
            cat: 'Results'
        },
        78: {
            key: 'n',
            fun: pageButtonClick(1),
            des: 'go to next page',
            cat: 'Results'
        },
        79: {
            key: 'o',
            fun: openResult(false),
            des: 'open search result',
            cat: 'Results'
        },
        84: {
            key: 't',
            fun: openResult(true),
            des: 'open the result in a new tab',
            cat: 'Results'
        },
        82: {
            key: 'r',
            fun: reloadPage,
            des: 'reload page from the server',
            cat: 'Control'
        },
        72: {
            key: 'h',
            fun: toggleHelp,
            des: 'toggle help window',
            cat: 'Other'
        }
    };

    $(document).keydown(function(e) {
        // check for modifiers so we don't break browser's hotkeys
        if (vimKeys.hasOwnProperty(e.keyCode)
            && !e.ctrlKey
            && !e.altKey
            && !e.shiftKey
            && !e.metaKey)
        {
            if (e.keyCode === 27) {
                if (e.target.tagName.toLowerCase() === 'input') {
                    vimKeys[e.keyCode].fun();
                }
            } else {
                if (e.target === document.body) {
                    e.preventDefault();
                    vimKeys[e.keyCode].fun();
                }
            }
        }
    });

    function nextResult(current, direction) {
        var next = current[direction]();
        while (!next.is('.result') && next.length !== 0) {
            next = next[direction]();
        }
        return next
    }

    function highlightResult(which) {
        return function() {
            var current = $('.result[data-vim-selected]');
            if (current.length === 0) {
                current = $('.result:first');
                if (current.length === 0) {
                    return;
                }
            }

            var next;

            if (typeof which !== 'string') {
                next = which;
            } else {
                switch (which) {
                    case 'visible':
                        var top = $(window).scrollTop();
                        var bot = top + $(window).height();
                        var results = $('.result');

                        for (var i = 0; i < results.length; i++) {
                            next = $(results[i]);
                            var etop = next.offset().top;
                            var ebot = etop + next.height();

                            if ((ebot <= bot) && (etop > top)) {
                                break;
                            }
                        }
                        break;
                    case 'down':
                        next = nextResult(current, 'next');
                        if (next.length === 0) {
                            next = $('.result:first');
                        }
                        break;
                    case 'up':
                        next = nextResult(current, 'prev');
                        if (next.length === 0) {
                            next = $('.result:last');
                        }
                        break;
                    case 'bottom':
                        next = $('.result:last');
                        break;
                    case 'top':
                    default:
                        next = $('.result:first');
                }
            }

            if (next) {
                current.removeAttr('data-vim-selected').removeClass('well well-sm');
                next.attr('data-vim-selected', 'true').addClass('well well-sm');
                scrollPageToSelected();
            }
        }
    }

    function reloadPage() {
        document.location.reload(false);
    }

    function removeFocus() {
        if (document.activeElement) {
            document.activeElement.blur();
        }
    }

    function pageButtonClick(num) {
        return function() {
            var buttons = $('div#pagination button[type="submit"]');
            if (buttons.length !== 2) {
                console.log('page navigation with this theme is not supported');
                return;
            }
            if (num >= 0 && num < buttons.length) {
                buttons[num].click();
            } else {
                console.log('pageButtonClick(): invalid argument');
            }
        }
    }

    function scrollPageToSelected() {
        var sel = $('.result[data-vim-selected]');
        if (sel.length !== 1) {
            return;
        }

        var wnd = $(window);

        var wtop = wnd.scrollTop();
        var etop = sel.offset().top;

        var offset = 30;

        if (wtop > etop) {
            wnd.scrollTop(etop - offset);
        } else  {
            var ebot = etop + sel.height();
            var wbot = wtop + wnd.height();

            if (wbot < ebot) {
                wnd.scrollTop(ebot - wnd.height() + offset);
            }
        }
    }

    function scrollPage(amount) {
        return function() {
            window.scrollBy(0, amount);
            highlightResult('visible')();
        }
    }

    function scrollPageTo(position, nav) {
        return function() {
            window.scrollTo(0, position);
            highlightResult(nav)();
        }
    }

    function searchInputFocus() {
        $('input#q').focus();
    }

    function openResult(newTab) {
        return function() {
            var link = $('.result[data-vim-selected] .result_header a');
            if (link.length) {
                var url = link.attr('href');
                if (newTab) {
                    window.open(url);
                } else {
                    window.location.href = url;
                }
            }
        };
    }

    function toggleHelp() {
        var helpPanel = $('#vim-hotkeys-help');
        if (helpPanel.length) {
            helpPanel.toggleClass('hidden');
            return;
        }

        var categories = {};

        for (var k in vimKeys) {
            var key = vimKeys[k];
            categories[key.cat] = categories[key.cat] || [];
            categories[key.cat].push(key);
        }

        var sorted = Object.keys(categories).sort(function(a, b) {
            return categories[b].length - categories[a].length;
        });

        if (sorted.length === 0) {
            return;
        }

        var html = '<div id="vim-hotkeys-help" class="well vim-hotkeys-help">';
        html += '<div class="container-fluid">';

        html += '<div class="row">';
        html += '<div class="col-sm-12">';
        html += '<h3>How to navigate searxng with Vim-like hotkeys</h3>';
        html += '</div>'; // col-sm-12
        html += '</div>'; // row

        for (var i = 0; i < sorted.length; i++) {
            var cat = categories[sorted[i]];

            var lastCategory = i === (sorted.length - 1);
            var first = i % 2 === 0;

            if (first) {
                html += '<div class="row dflex">';
            }
            html += '<div class="col-sm-' + (first && lastCategory ? 12 : 6) + ' dflex">';

            html += '<div class="panel panel-default iflex">';
            html += '<div class="panel-heading">' + cat[0].cat + '</div>';
            html += '<div class="panel-body">';
            html += '<ul class="list-unstyled">';

            for (var cj in cat) {
                html += '<li><kbd>' + cat[cj].key + '</kbd> ' + cat[cj].des + '</li>';
            }

            html += '</ul>';
            html += '</div>'; // panel-body
            html += '</div>'; // panel
            html += '</div>'; // col-sm-*

            if (!first || lastCategory) {
                html += '</div>'; // row
            }
        }

        html += '</div>'; // container-fluid
        html += '</div>'; // vim-hotkeys-help

        $('body').append(html);
    }
});
