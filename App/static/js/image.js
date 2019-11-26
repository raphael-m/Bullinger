
/* Zoom/Fit
 * -------- */
var h0 = 6978;  /* reference height/width */
var w0 = 9860;
var s = 0.1; /* --> {0.9, 1.1} step widths */

/* original sizes */
var _IMAGE_LOADED = 0;
var _IMAGE_WIDTH;
var _IMAGE_HEIGHT;
var _CONTAINER_WIDTH;
var _CONTAINER_HEIGHT;

$(document).ready( function() {
    if($('#card_drag').get(0).complete) {
        ImageLoaded();
    } else {
        $('#card_drag').on('load', function() {
            ImageLoaded();
        });
    }
    function ImageLoaded() {
        _IMAGE_WIDTH = $("#card_drag").width();
        _IMAGE_HEIGHT = $("#card_drag").height();
        _IMAGE_LOADED = 1;
        _CONTAINER_WIDTH = $("#card_image").outerWidth();
        _CONTAINER_HEIGHT = $("#card_image").outerHeight();
    }
});

/* Buttons */
$(document).ready( function() {
    $('#save_changes').click( function() {
        /* alert("Datenbank noch nicht einsatzbereit."); */
    });
});

/* Zoom */
$(document).ready( function() {
    $('#zoom_out').click( function() {
        _IMAGE_WIDTH = _IMAGE_WIDTH*(1-s);
        _IMAGE_HEIGHT = _IMAGE_HEIGHT*(1-s);
        $("#card_drag").height(_IMAGE_HEIGHT);
        $("#card_drag").width(_IMAGE_WIDTH);
        center();
    });
});

$(document).ready( function() {
    $('#zoom_in').click( function() {
        _IMAGE_WIDTH = _IMAGE_WIDTH*(1+s);
        _IMAGE_HEIGHT = _IMAGE_HEIGHT*(1+s);
        $("#card_drag").height(_IMAGE_HEIGHT);
        $("#card_drag").width(_IMAGE_WIDTH);
        center();
    });
});

/* Fit */
$(document).ready( function() {
    $('#fit_width').click( function() {
        _IMAGE_WIDTH = _CONTAINER_WIDTH;
        _IMAGE_HEIGHT = h0/w0*_IMAGE_WIDTH;
        $("#card_drag").height(_IMAGE_HEIGHT);
        $("#card_drag").width(_IMAGE_WIDTH);
        $("#card_drag").css({ top: 0 + 'px', left: 0 + 'px' });
        center();
    });
});

$(document).ready( function() {
    $('#fit_height').click( function() {
        _IMAGE_HEIGHT = _CONTAINER_HEIGHT;
        _IMAGE_WIDTH = w0/h0*_IMAGE_HEIGHT;
        $("#card_drag").height(_IMAGE_HEIGHT);
        $("#card_drag").width(_IMAGE_WIDTH);
        $("#card_drag").css({ top: 0 + 'px', left: 0 + 'px' });
        center();
    });
});

function center() {
    var overhang_h = _CONTAINER_HEIGHT - _IMAGE_HEIGHT;
    var overhang_w = _CONTAINER_WIDTH - _IMAGE_WIDTH;
    if(overhang_w >= 0) { $("#card_drag").css({ left: overhang_w/2 + 'px' }); }
    if(overhang_h >= 0) { $("#card_drag").css({ top: overhang_h/2 + 'px' }); }
    save_values();
}

function save_values() {
    h0 = $("#card_drag").height();
    w0 = $("#card_drag").width();
    $('#img_height').val(h0);
    $('#img_width').val(w0);
}

/* Dragging */
$(document).ready( function() {

    var _DRAGGING_STARTED = 0;
    var _LAST_MOUSE_POSITION = { x: null, y: null };
    var _DIV_OFFSET = $('#card_image').offset();

    $('#card_image').on('mouseup', function() {
        _DRAGGING_STARTED = 0;
    });

    $('#card_image').on('mousedown', function(event) {
        if(_IMAGE_LOADED == true) {
            _DRAGGING_STARTED = 1;
            _LAST_MOUSE_POSITION = { x: event.pageX - _DIV_OFFSET.left, y: event.pageY - _DIV_OFFSET.top };
        }
    });

    $('#card_image').on('mousemove', function(event) {
        if(_DRAGGING_STARTED == 1) {
            var current_mouse_position = { x: event.pageX - _DIV_OFFSET.left, y: event.pageY - _DIV_OFFSET.top };
            var change_x = current_mouse_position.x - _LAST_MOUSE_POSITION.x;
            var change_y = current_mouse_position.y - _LAST_MOUSE_POSITION.y;
            _LAST_MOUSE_POSITION = current_mouse_position;

            var img_top = parseInt($("#card_drag").css('top'), 10);
            var img_left = parseInt($("#card_drag").css('left'), 10);
            var img_top_new = img_top + change_y;
            var img_left_new = img_left + change_x;

            var overhang_h =_CONTAINER_HEIGHT - _IMAGE_HEIGHT;
            var overhang_w = _CONTAINER_WIDTH - _IMAGE_WIDTH;

            /* if the page is bigger than its container */
            if(img_left_new <= overhang_w & overhang_w <= 0) { img_left_new = overhang_w; }
            if(img_left_new > 0 & overhang_w <= 0) { img_left_new = 0; }
            if(img_top_new > 0 & overhang_h <= 0) { img_top_new = 0; }
            if(img_top_new <= overhang_h & overhang_h <= 0) { img_top_new = overhang_h; }

            /* if the page is smaller... */
            if(overhang_w >= 0) { img_left_new = overhang_w/2; }
            if(overhang_h >= 0) { img_top_new = overhang_h/2; }

            $("#card_drag").css({ top: img_top_new + 'px', left: img_left_new + 'px' });
        }
    });
});

/* Resize  */
$(document).ready( function() {

    var DRAG_START = 0;
    var LAST_MOUSE_POSITION = { x: null, y: null };
    var OFFSET = $('#card_options').offset();

    $(document).on('mouseup', function() {
        DRAG_START = 0;
        $('#image_height_value').val($("#card_image").outerHeight());
    });

    $('#is_movable').on('mousedown', function(event) {
        DRAG_START = 1;
        LAST_MOUSE_POSITION = event.pageY - OFFSET.top;
    });

    $('#card_options2').on('mousedown', function(event) {
        DRAG_START = 1;
        LAST_MOUSE_POSITION = event.pageY - OFFSET.top;
    });

    $(window).on('mousemove', function(event) {
        if(DRAG_START == 1) {
            var current_mouse_position = event.pageY - OFFSET.top;
            var change_y = current_mouse_position - LAST_MOUSE_POSITION;
            LAST_MOUSE_POSITION = current_mouse_position;
            h = parseInt($('#card_image').height());
            $('#card_image').height(h+change_y);
            _CONTAINER_WIDTH = $("#card_image").outerWidth();
            _CONTAINER_HEIGHT = $("#card_image").outerHeight();
        }
    });
});


/* MOVE */

var step = 50;
var time = 100;

/* right, left, up, down */
$(document).ready( function() {
    $('#move_right').click( function() {
        if (_CONTAINER_WIDTH < _IMAGE_WIDTH) {
            l = parseInt($("#card_drag").css('left'), 10) - step;
            $("#card_drag").css({ left: l + 'px' });
            t = _CONTAINER_WIDTH - _IMAGE_WIDTH - parseInt($("#card_drag").css('left'));
            if(t > 0) { $("#card_drag").animate({ left: "+=" + t }, time ); }
            center();
        }
    });
});

var lock = false;
$(document).ready( function() {
    $('#move_left').click( function b() {
        if (_CONTAINER_WIDTH < _IMAGE_WIDTH) {
            l = parseInt($("#card_drag").css('left'), 10) + step;
            $("#card_drag").css({ left: l + 'px' });
            if(l > 0) { $("#card_drag").animate({ left: "-=" + l }, time ); }
            center();
        }
    });
});

function unlock() {
    lock = false;
}

$(document).ready( function() {
    $('#move_up').click( function() {
        t = parseInt($("#card_drag").css('top'), 10) + step;
        $("#card_drag").css({ top: t + 'px' });
        if(t > 0) { $("#card_drag").animate({ top: "+=" + -t }, time ); }
        center();
    });
});

$(document).ready( function() {
    $('#move_down').click( function() {
        t = parseInt($("#card_drag").css('top'), 10) - step;
        $("#card_drag").css({ top: t + 'px' });
        l = _CONTAINER_HEIGHT - _IMAGE_HEIGHT - parseInt($("#card_drag").css('top'));
        if(l > 0) { $("#card_drag").animate({ top: "+=" + l }, time ); }
        center();
    });
});


/* -most */
$(document).ready( function() {
    $('#move_rightmost').click( function() {
        t = _CONTAINER_WIDTH - _IMAGE_WIDTH;
        $("#card_drag").css({ left: t + 'px' });
        center();
    });
});

$(document).ready( function() {
    $('#move_leftmost').click( function() {
        $("#card_drag").css({ left: 0 + 'px' });
        center();
    });
});


$(document).ready( function() {
    $('#move_upmost').click( function() {
        $("#card_drag").css({ top: 0 + 'px' });
        center();
    });
});

$(document).ready( function() {
    $('#move_downmost').click( function() {
        t = _CONTAINER_HEIGHT - _IMAGE_HEIGHT;
        $("#card_drag").css({ top: t + 'px' });
        center();
    });
});

$(document).ready( function() {
    h = $('#image_height_value').val();
    $('#card_image').height(h);

    h = $('#img_height').val();
    w = $('#img_width').val();
    if (w != '100%') {
        $("#card_drag").height(h);
        $("#card_drag").width(w);
        _IMAGE_WIDTH = w;
        _IMAGE_HEIGHT = h;
    } else {
        $("#card_drag").width('100%');
        _IMAGE_WIDTH = $("#card_drag").width();
        _IMAGE_HEIGHT = $("#card_drag").height();
    }
    _CONTAINER_WIDTH = $("#card_image").outerWidth();
    _CONTAINER_HEIGHT = $("#card_image").outerHeight();
    center();
});

/* "Button" [+/-]
var is_extended = false;
$(document).ready( function() {
    $('#toggle_icon').click(function() {
        if(!(is_extended)){
            $('#toggle_icon').text('[-]');
        } else {
            $('#toggle_icon').text('[+]');
        } is_extended = !(is_extended);
    });
});
<span id="toggle_icon" class="pm_icon">[+]</span>
*/
