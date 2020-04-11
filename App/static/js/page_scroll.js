
/* FAQ */

var speed = 300;

$(document).ready(function () {
    $("#href_faq_adress").click( function (){
        var h = $("#faq_adress").offset().top;
        $("#body, html").animate({ scrollTop: h }, { duration: speed });
    });
});

$(document).ready(function () {
    $("#href_faq_date").click( function (){
        var h = $("#faq_date").offset().top;
        $("#body, html").animate({ scrollTop: h }, { duration: speed });
    });
});

$(document).ready(function () {
    $("#href_faq_copy").click( function (){
        var h = $("#faq_copy").offset().top;
        $("#body, html").animate({ scrollTop: h }, { duration: speed });
    });
});

$(document).ready(function () {
    $("#href_faq_lang").click( function (){
        var h = $("#faq_lang").offset().top;
        $("#body, html").animate({ scrollTop: h }, { duration: speed });
    });
});

$(document).ready(function () {
    $("#href_faq_state").click( function (){
        var h = $("#faq_state").offset().top;
        $("#body, html").animate({ scrollTop: h }, { duration: speed });
    });
});

$(document).ready(function () {
    $("#href_faq_var").click( function (){
        var h = $("#faq_var").offset().top;
        $("#body, html").animate({ scrollTop: h }, { duration: speed });
    });
});

/*.navigate_l, .navigate_t, .navigate_b, .navigate_r {*/

$(document).ready(function () {
    $(".navigate_t").click( function (){
        $("#body, html").animate({ scrollTop: "0px" }, { duration: speed });
    });
});

$(document).ready(function () {
    $(".navigate_r").click( function () {
        h = $(this).parent().parent().parent().next().next().find(">:first-child").offset().top;
        $("#body, html").animate({ scrollTop: h }, { duration: speed });
    });
});

$(document).ready(function () {
    $(".navigate_l").click( function () {
        h = $(this).parent().parent().parent().prev().prev().find(">:first-child").offset().top;
        $("#body, html").animate({ scrollTop: h }, { duration: speed });
    });
});

/* stats */

$(document).ready(function () {
    $("#href_stats_rank").click( function (){
        var h = $("#stats_rank").offset().top;
        $("#body, html").animate({ scrollTop: h }, { duration: speed });
    });
});

$(document).ready(function () {
    $("#href_stats_changes").click( function (){
        var h = $("#stats_changes").offset().top;
        $("#body, html").animate({ scrollTop: h }, { duration: speed });
    });
});

$(document).ready(function () {
    $("#href_stats_activity").click( function (){
        var h = $("#stats_activity").offset().top;
        $("#body, html").animate({ scrollTop: h }, { duration: speed });
    });
});
