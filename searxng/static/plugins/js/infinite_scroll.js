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
