function popup(url, w, h) {
    w = window.open(url, "Preview", "height=" + h +", width=" + w +", screenX=500, screenY=150, scrollbars=yes, resizable=yes");
    w.focus();
}

function set_focus() {
    $("#core_data input:first").focus();
    $("#data input:first").focus();
    $("#seo_data input:first").focus();
}

function create_menu() {
    $('ul.sf-menu').superfish({
        speed: "fast",
        delay: "200"
    });
};

function set_tab() {
    var cookiestr = $.cookie("tab");

    if (!cookiestr) {
        cookiestr = "0|0";
    }

    var array = cookiestr.split("|");

    var portal2object = [0, 2, 3, 4, 5, 8]
    var object2portal = [0, 0, 1, 2, 3, 4, 0, 0, 5]

    var is_portal = $("#portal").length
    var index = parseInt(array[1]);

    if (parseInt(array[0]) != is_portal) {
        if (is_portal) {
            index = object2portal[index];
        }
        else {
            index = portal2object[index];
        }
    }

    $('#manage-tabs').tabs('select', index)
}

function create_tabs() {
    $('#manage-tabs').tabs();

    $('#manage-tabs').bind('tabsshow', function(event, ui) {
        set_focus();
        var cookiestr = $("#portal").length + "|" + ui.index
        $.cookie("tab", cookiestr);
    });

    set_tab();
}

// Loads passed url per ajax and replaces returned chunks of HTML
function load_url(url, tabs) {
    show_ajax_loading();
    $.get(url, function(data) {
        data = $.parseJSON(data);
        for (var html in data["html"])
            $(data["html"][html][0]).html(data["html"][html][1]);

        create_menu();

        if (tabs) {
            create_tabs();
        }

        if (data["message"])
            show_message(data["message"])

        hide_ajax_loading();
        set_focus();
    })
};

function hide_ajax_loading() {
    $(".ajax-loading").hide();
};

function show_ajax_loading() {
    $(".ajax-loading").show();
};

function show_message(message) {
    $.jGrowl(message);
    $.cookie("message", null, { path: '/' });
}

$(function() {
    update_editor();
    overlay = $("#overlay").overlay({
        closeOnClick: false,
        oneInstance: false,
        api:true,
        speed:1,
        expose: {color: '#222', loadSpeed:1 },
        onClose: function() { set_focus(); },
    });

    overlay_2 = $("#overlay-2").overlay({
        closeOnClick: false,
        oneInstance: false,
        api:true,
        speed:1,
        expose: {color: '#222', loadSpeed:1 }
    });

    // Message
    var message = $.cookie("message");
    if (message)
        show_message(message);

    create_menu();
    create_tabs();

    // Class which closes the overlay.
    $(".overlay-close").live("click", function() {
        overlay.close()
        set_focus();
        return false;
    });

    // Generic ajax save button
    $(".ajax-submit").live("click", function() {
        var clicked = $(this);
        if (clicked.hasClass("display-loading"))
            show_ajax_loading();

        var action = $(this).attr("name");
        var obj_id = $("#obj-id").attr("data");

        $(this).parents("form:first").ajaxSubmit({
            data : { "action" : action, "obj-id" : obj_id },
            dataType: "json",
            success : function(data) {
                for (var html in data["html"])
                    $(data["html"][html][0]).html(data["html"][html][1]);

                create_menu()

                if (data["message"])
                    show_message(data["message"]);

                if (data["open_overlay"])
                    overlay.load()

                if (data["close_overlay"])
                    overlay.close()

                if (data["url"])
                    window.location = data["url"];

                if (data["tab"] != undefined)
                    $('#manage-tabs').tabs('select', parseInt(data["tab"]));

                // if current view is given we upload an image or file to the
                // current object
                if (data["current_view"]) {
                    display_content();
                }
                else {
                    // Don't update the editor when we upload an image or a file,
                    // Otherwise the selected text is lost within the textarea
                    // and insert would not work.
                    update_editor();
                }

                if (clicked.hasClass("display-loading"))
                    hide_ajax_loading();

            }
        })
        return false;
    });

    // Generic ajax link
    $(".ajax-link").live("click", function() {
        update_editor();
        show_ajax_loading();
        var url = $(this).attr("href");

        $.get(url, function(data) {
            data = $.parseJSON(data);
            for (var html in data["html"])
                $(data["html"][html][0]).html(data["html"][html][1]);

            create_menu()

            if (data["message"])
                show_message(data["message"]);

            if (data["open_overlay"]) {
                overlay.load();
                $("#overlay input:first").focus();
            }

            if (data["close_overlay"]) {
                overlay.close()
                set_focus();
            }

            if (data["tabs"])
                create_tabs()

            hide_ajax_loading();
            update_editor();
        });

        return false;
    });

    // User filter
    $(".reset-link").live("click", function() {
        $("input[name=name_filter]").val("");
        $("select[name=active_filter]").val("");
        return false;
    });

    $(".user-name-filter").live("keyup", function() {
        var url = $(this).attr("data");
        var value = $(this).attr("value");
        $.get(url, { "user_name_filter" : value }, function(data) {
            data = $.parseJSON(data);
            for (var html in data["html"])
                $(data["html"][html][0]).html(data["html"][html][1]);
        });
    });

    // Generic select all checkboxes class: selects all checkboxes with class
    // "select-xxx" where xxx is the value of the select-all checkbox.
    $(".select-all").live("click", function() {
        var checked = this.checked;
        var selector = ".select-" + $(this).attr("value")
        $(selector).each(function() {
            this.checked = checked;
        });
    });

    // Delete dialog
    var delete_dialog = $("#yesno").overlay({ closeOnClick: false, api:true, loadSpeed: 200, top: '25%', expose: {color: '#222', loadSpeed:100 } });
    $(".delete-link").live("click", function() {
        $("#delete-url").html($(this).attr("href"));
        $("#delete-is-ajax").html($(this).attr("is_ajax"));
        delete_dialog.load();
        return false;
    });

    var buttons = $("#yesno button").live("click", function(e) {
        delete_dialog.close();
        var yes = buttons.index(this) === 0;
        var url = $("#delete-url").html();
        var is_ajax = $("#delete-is-ajax").html();
        if (yes) {
            if (is_ajax == "1") {
                $.get(url, function(data) {
                    data = $.parseJSON(data);
                    for (var html in data["html"])
                        $(data["html"][html][0]).html(data["html"][html][1]);
                    if (data["message"])
                        show_message(data["message"])
               });
            }
            else
                window.location.href = url;
        }
    });
});

$(document).ajaxSend(function(event, xhr, settings) {
    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", $.cookie("csrftoken"));
    }
});
