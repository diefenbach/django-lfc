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
    $('ul.sf-menu').each(function(index) {
        $(this).superfish({
            speed: "fast",
            delay: "200"
        });
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

    $('#manage-tabs').tabs('option', "active", index)
};

function create_buttons() {
    $("input[type=submit], input[type=file], .overlay-close").button();
    $("select").selectmenu();
};

function create_tabs() {
    $('#manage-tabs').tabs({
        load: function(event, ui) {
            create_buttons();
        }
    });
    $('#manage-tabs').css("display", "block");

    $('#manage-tabs').on('tabsactivate', function(event, ui) {
        set_focus();
        var cookiestr = $("#portal").length + "|" + ui.newTab.index();
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
    $.removeCookie('message', { path: '/' });
}

String.prototype.hashCode = function() {
    var hash = 0, i, chr, len;
    if (this.length == 0) return hash;
    for (i = 0, len = this.length; i < len; i++) {
        chr   = this.charCodeAt(i);
        hash  = ((hash << 5) - hash) + chr;
        hash |= 0;
    }
    return Math.abs(hash);
};

function bind_datetime_picker(language) {
    $(".vDateField").datepicker({
      showWeek: true,
      firstDay: 1,
      dateFormat: "yy-mm-dd",
    });

    $(".vTimeField").timepicker({
        timeFormat: "H:i",
        maxTime: "23:30",
        scrollDefaultNow: true,
    });

    if (language != "en") {
        $.getScript("/static/lfc/jquery-ui-1.11.0/i18n/datepicker-" + language + ".js", function(){
            $(".vDateField").datepicker($.datepicker.regional[language]);
        });
    };
};

function bind_fileupload(prefix) {
    $('#' + prefix + 'upload').fileupload({
        dataType: 'xml',
        progressInterval: 3,
        start: function(e) {
            $("." + prefix + "-progress-title").css("display", "block");
        },
        add: function(e, data) {
            $("#"+ prefix + "-progress").append('<div id="' + data.files[0].name.hashCode() + '" class="bar"><div class="progress-label">' + data.files[0].name + '</div></div>');
            data.submit();
        },
        progress: function (e, data) {
            var progress = parseInt(data.loaded / data.total * 100, 10);
            var name = data.files[0].name.hashCode();
            var progressbar = $('#' + name);
            var progress_label = $('#' + name + " .progress-label");
            progressbar.progressbar({
                value: progress,
                change: function() {
                    progress_label.text(data.files[0].name + " - " + progressbar.progressbar("value") + "%");
                },
            });
        },
        progressall: function (e, data) {
            if (data.loaded == data.total) {
                $("." + prefix + "-progress-title").css("display", "none");
                $("." + prefix + "-progress-title-2").css("display", "block");
            };
            var progress = parseInt(data.loaded / data.total * 100, 10);

            var progressbar = $("#" + prefix + "-progressall");
            var progress_label = $("#" + prefix + "-progressall .progress-label");

            progressbar.progressbar({
                value: progress,
                change: function() {
                    progress_label.text(" Total - " + progressbar.progressbar("value") + "%");
                },
            });
        },
        stop: function(e) {
            var url = $("#" + prefix + "s-form").attr("data");
            $.get(url, function(data) {
                data = $.parseJSON(data);
                $("#" + prefix + "s").html(data["html"]);
                $.jGrowl(data["message"]);
            });
        }
    });
};

$(function() {
    create_tabs();
    create_buttons();
    update_editor();
    create_menu();

    $("#overlay").dialog({
        autoOpen: false,
        resizable: false,
        draggable: true,
        position: { my: "bottom", at: "center"},
        width: 900,
        modal: true,
        close: function( event, ui ) {
            set_focus();
        }
    });

    // Message
    var message = $.cookie("message");
    if (message)
        show_message(message);

    // Generic ajax save button
    $(document).on("click", ".ajax-submit", function() {
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
                    $("#overlay").dialog("open");

                if (data["close_overlay"])
                    $("#overlay").dialog("close");

                if (data["url"])
                    window.location = data["url"];

                if (data["tab"] != undefined)
                    $('#manage-tabs').tabs('option', 'active', parseInt(data["tab"]));

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
    $(document).on("click", ".ajax-link", function() {
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
                $("#overlay").dialog("open");
                $("#overlay input:first").focus();
            }

            if (data["close_overlay"]) {
                $("#overlay").dialog("close");
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
    $(document).on("click", ".reset-link", function() {
        $("input[name=name_filter]").val("");
        $("select[name=active_filter]").val("");
        return false;
    });

    $(document).on("keyup", ".user-name-filter", function() {
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
    $(document).on("click", ".select-all", function() {
        var checked = this.checked;
        var selector = ".select-" + $(this).attr("value")
        $(selector).each(function() {
            this.checked = checked;
        });
    });

    // Delete dialog
    $("#yesno").dialog({
        autoOpen: false,
        resizable: false,
        draggable: false,
        position: { my: "bottom", at: "center"},
        width: 300,
        modal: true,
        buttons: [
            {
                text: "Yes",
                click: function() {
                    var url = $("#delete-url").html();
                    var is_ajax = $("#delete-is-ajax").html();
                    if (is_ajax == "1") {
                        $.get(url, function(data) {
                            data = $.parseJSON(data);
                            for (var html in data["html"])
                                $(data["html"][html][0]).html(data["html"][html][1]);
                            if (data["message"])
                                show_message(data["message"])
                       });
                    }
                    else {
                        window.location.href = url;
                    }
                }
            },
            {
                text: "No",
                click: function() {
                    $(this).dialog("close");
                }
            }
        ],
        close: function(event, ui) {
            set_focus();
        }
    });

    $(document).on("click", ".delete-link", function() {
        $("#delete-url").html($(this).attr("href"));
        $("#delete-is-ajax").html($(this).attr("is_ajax"));
        $("#yesno").dialog("open");
        return false;
    });

    $(document).on("click", ".overlay-close", function() {
        $("#overlay").dialog("close");
    });

    $(document).ajaxStop(function() {
        create_buttons();
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
