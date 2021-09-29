$(document).ready(function() {
    if($('#q').length) {
        $('#categories label').click(function(e) {
            $('#categories input[type="checkbox"]').each(function(i, checkbox) {
                $(checkbox).prop('checked', false);
            });
            $(document.getElementById($(this).attr("for"))).prop('checked', true);
            if($('#q').val()) {
                if (getHttpRequest() == "GET") {
                    $('#search_form').attr('action', $('#search_form').serialize());
                }
                $('#search_form').submit();
            }
            return false;
        });
        $('#time-range').change(function(e) {
            if($('#q').val()) {
                if (getHttpRequest() == "GET") {
                    $('#search_form').attr('action', $('#search_form').serialize());
                }
                $('#search_form').submit();
            }
        });
        $('#language').change(function(e) {
            if($('#q').val()) {
                if (getHttpRequest() == "GET") {
                    $('#search_form').attr('action', $('#search_form').serialize());
                }
                $('#search_form').submit();
            }
        });
    }
});

function getHttpRequest() {
    httpRequest = "POST";
    urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('method')) {
        httpRequest = urlParams.get('method');
    }
    return httpRequest;
}
