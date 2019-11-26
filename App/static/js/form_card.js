var val = {};

$(document).ready( function() {
    $('input').focus( function() {
        if( $(this).css('color') === "rgb(192, 192, 192)") {
            $(this).removeClass('card_input');
            $(this).addClass('card_input_content');
            val[$(this).attr('id')] = $(this).val();
            $(this).val('');
        }
    });
});

$(document).ready( function() {
    $('input').focusout( function() {
        if($(this).val() === '') {
            $(this).removeClass('card_input_content');
            $(this).addClass('card_input');
            $(this).val(val[$(this).attr('id')]);
        }
    });
});

/*
$(document).ready( function() {
    $('textarea').focus( function() {
        if( $(this).css('color') === "rgb(192, 192, 192)") {
            $(this).removeClass('card_input');
            $(this).addClass('card_input_content');
            val[$(this).attr('id')] = $(this).val();
            $(this).val('');
        }
    });
});

$(document).ready( function() {
    $('textarea').focusout( function() {
        if($(this).val() === '') {
            $(this).removeClass('card_input_content');
            $(this).addClass('card_input');
            $(this).val(val[$(this).attr('id')]);
        }
    });
});
*/