/* Button: Start */
$(document).ready( function() {
    $('#dropDown').click( function() {
        $('.drop-down').toggleClass('drop-down--active');
        if(this.getAttribute('class') == "drop-down__button") {
            $('#dropDown').removeClass('drop-down__button');
            $('#dropDown').addClass('drop-down__button_clicked');
            $('#dropDownButtonName').removeClass('drop-down__name');
            $('#dropDownButtonName').addClass('drop-down__name_clicked');
        } else  {
            $('#dropDown').removeClass('drop-down__button_clicked');
            $('#dropDown').addClass('drop-down__button');
            $('#dropDownButtonName').removeClass('drop-down__name_clicked');
            $('#dropDownButtonName').addClass('drop-down__name');
        }
    });
});

$(document).ready( function() {
    $('.drop-down__menu-box').mouseleave( function() {
        closeStart();
    });
});

$(document).ready( function() {
    $(document).keyup( function(e) {
        if (e.key === "Escape") closeStart();
    });
});

function closeStart() {
    $('.drop-down').toggleClass('drop-down--active', false);
    $('#dropDown').removeClass('drop-down__button_clicked');
    $('#dropDown').addClass('drop-down__button');
    $('#dropDownButtonName').removeClass('drop-down__name_clicked');
    $('#dropDownButtonName').addClass('drop-down__name');
}


/* Load Pages: Login/Register/Admin */
$(document).ready( function() {
    $('#start_login').click( function() {
        $.get("/login", function(page) {
            $('#main').html(page);
            closeStart();
        });
    });
});

$(document).ready( function() {
    $('#start_register').click( function() {
        $.get("/register", function(page) {
            $('#main').html(page);
            closeStart();
        });
    });
});

$(document).ready( function() {
    $('#start_admin').click( function() {
        $.get("/admin", function(page) {
            $('#main').html(page);
            closeStart();
        });
    });
});



/* Login */
$(document).ready( function() {

});


/* Register */
$(document).ready(function() {

});


/* Admin */
$(document).ready(function() {

});
