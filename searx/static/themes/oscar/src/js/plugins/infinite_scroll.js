if (searxng.plugins['searx.plugins.infinite_scroll']) {
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

    $(document).ready(function() {
        var win = $(window);
        if(!hasScrollbar()) {
            loadNextPage();
        }
        win.scroll(function() {
            $("#pagination button").css("visibility", "hidden");
            if ($(document).height() - win.height() - win.scrollTop() < 150) {
                loadNextPage();
            }
        });
    });

    const style = document.createElement('style');
    style.textContent = `
    @keyframes rotate-forever {
        0%   { transform: rotate(0deg) }
        100% { transform: rotate(360deg) }
    }
    .loading-spinner {
        animation-duration: 0.75s;
        animation-iteration-count: infinite;
        animation-name: rotate-forever;
        animation-timing-function: linear;
        height: 30px;
        width: 30px;
        border: 8px solid #666;
        border-right-color: transparent;
        border-radius: 50% !important;
        margin: 0 auto;
    }
    #pagination button {
        visibility: hidden;
    }
    `;
    document.head.append(style);
}
