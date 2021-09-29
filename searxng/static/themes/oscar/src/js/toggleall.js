$(document).ready(function(){
    $("#allow-all-engines").click(function() {
        $(".onoffswitch-checkbox").each(function() { this.checked = false;});
    });

    $("#disable-all-engines").click(function() {
        $(".onoffswitch-checkbox").each(function() { this.checked = true;});
    });
});

