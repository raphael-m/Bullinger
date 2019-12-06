
/* Menu
 * ---- */
$(document).ready( function() {
    $('#menu_home').click( function() {
        window.location.replace("/index");
    });
});

$(document).ready( function() {
    $('#menu_cards').click( function() {
        window.location.replace("/overview");
    });
});

$(document).ready( function() {
    $('#menu_stats').click( function() {
        window.location.replace("/stats");
    });
});

$(document).ready( function() {
    $('#menu_gateway').click( function() {
        window.location.replace("/quick_start");
    });
});

/* Account
 * ------- */
$(document).ready( function() {
    $('#start_login').click( function() {
        window.location.replace("/login")
    });
});

$(document).ready( function() {
    $('#start_logout').click( function() {
        window.location.replace("/logout")
    });
});

$(document).ready( function() {
    $('#start_register').click( function() {
        window.location.replace("/register")
    });
});

$(document).ready( function() {
    $('#start_admin').click( function() {
        window.location.replace("/admin")
    });
});
