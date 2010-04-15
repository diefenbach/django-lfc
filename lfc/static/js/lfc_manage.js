function CustomFileBrowser(field_name, url, type, win) {

    url = "/manage/filebrowser?obj_id=" + $("#obj-id").attr("data"),
    url = url + "&type=" + type;

    tinyMCE.activeEditor.windowManager.open({
        file: url,
        width: 820,  // Your dimensions may differ - toy around with them!
        height: 500,
        resizable: "yes",
        scrollbars: "yes",
        inline: "no",
        close_previous: "no"
    }, {
        window: win,
        input: field_name,
        editor_id: tinyMCE.selectedInstance.editorId
    });
    return false;
}

tinyMCE.init({
    mode: "none",
    theme : "advanced",
    height : "400",
    tab_focus : ":prev,:next",
    button_tile_map : true,
    plugins : "advimage, safari, fullscreen",
    convert_urls : false,
    theme_advanced_buttons1 : "bold, italic, underline, |, justifyleft," +
                              "justifycenter, justifyright, justifyfull, |," +
                              "bullist,numlist, |, outdent, indent, |, image, |, undo," +
                              "redo, |, code, link, unlink, styleselect, formatselect, |," +
                              "removeformat, fullscreen",
    theme_advanced_buttons2: "",
    theme_advanced_buttons3: "",
    theme_advanced_buttons4: "",
    theme_advanced_toolbar_location : "top",
    theme_advanced_toolbar_align : "left",
    content_css : "/media/tiny.css",
    file_browser_callback: "CustomFileBrowser",
})

$(function() {

    // Message
    var message = $.cookie("message");

    if (message) {
        $.jGrowl(message);
        $.cookie("message", null, { path: '/' });
    };
    
    //  Menu
    $('ul.sf-menu').superfish({
        speed: "fast",
        delay: "200"
    });

    // //  Dialog
    // $("#dialog").dialog({
    //     autoOpen: false,
    //     closeOnEscape: true,
    //     modal: true,
    //     width: 800,
    //     height: 600,
    //     overlay: {
    //         opacity: 0.7,
    //         background: "black"
    //     }
    // });

    // Tabs
    $('#manage-tabs > ul').tabs({ cookie: { expires: 30 } });

    // Generic ajax save button
    $(".ajax-save-button").livequery("click", function() {
        $(".ajax-loading").show()
        var action = $(this).attr("name")
        tinyMCE.execCommand('mceRemoveControl', false, 'id_text');
        tinyMCE.execCommand('mceRemoveControl', false, 'id_short_text');
        $(this).parents("form:first").ajaxSubmit({
            data : {"action" : action},
            success : function(data) {
                data = JSON.parse(data);
                for (var html in data["html"])
                    $(data["html"][html][0]).html(data["html"][html][1]);
                tinyMCE.execCommand('mceAddControl', true, 'id_text');
                tinyMCE.execCommand('mceAddControl', true, 'id_short_text');
                $('ul.sf-menu').superfish({
                    speed: "fast",
                    delay: "200"
                });
                if (data["message"])
                    $.jGrowl(data["message"]);
                $(".ajax-loading").hide();
            }
        })
        return false;
    });
    
    // Generic ajax link
    $(".ajax-link").livequery("click", function() {
        var url = $(this).attr("href");

        $.get(url, function(data) {
            data = JSON.parse(data);
            for (var html in data["html"])
                $(data["html"][html][0]).html(data["html"][html][1]);

            if (data["message"]) {
                $.jGrowl(data["message"]);
            }
        });

        return false;
    });

    $(".reset-link").livequery("click", function() {
        $("input[name=name_filter]").val("");
        $("select[name=active_filter]").val("");
        return false;
    });

    $(".user-name-filter").livequery("keyup", function() {
        var url = $(this).attr("data");
        var value = $(this).attr("value");
        $.get(url, { "user_name_filter" : value }, function(data) {
            data = JSON.parse(data);
            for (var html in data["html"])
                $(data["html"][html][0]).html(data["html"][html][1]);
        });
    });

    // Confirmation link
    var confirmation;
    $(".confirmation-link-no").livequery("click", function() {
        $(this).parent().replaceWith(confirmation);
        return false;
    });

    $(".confirmation-link").livequery("click", function() {
        confirmation = $(this);
        var url = $(this).attr("href");
        var data = $(this).attr("data");
        var cls = $(this).attr("class");
        $(this).replaceWith("<span><span class='" + cls + "'>" + data + "</span> <a href='" + url + "'>Yes</a> <a class='confirmation-link-no' href=''>No</a></span>");
        return false;
    });

    // Page / Images
    $(".upload-file").livequery("change", function() {
        var name = $(this).attr("name");
        var number = parseInt(name.split("_")[1])
        number += 1;
        $(this).parent().after("<div><input type='file' class='upload-file' name='file_" + number + "' /></div>");
    });

    $("#page-images-save-button").livequery("click", function() {
        $("#page-images-form").ajaxSubmit({
            target : "#images"
        });
        return false;
    });

    $(".object-images-update-button").livequery("click", function() {
        var action = $(this).attr("name")
        $("#object-images-update-form").ajaxSubmit({
            data : {"action" : action},
            success : function(data) {
                var data = JSON.parse(data)
                $("#images").html(data["images"]);
                $.jGrowl(data["message"]);
            }
        });
        return false;
    });

    // Page / Files
    // Todo: merge this with Pages / Images

    $("#object-files-save-button").livequery("click", function() {
        $("#object-files-form").ajaxSubmit({
            target : "#files"
        });
        return false;
    });

    $(".object-files-update-button").livequery("click", function() {
        var action = $(this).attr("name")
        $("#object-files-update-form").ajaxSubmit({
            data : {"action" : action},
            success : function(data) {
                var data = JSON.parse(data)
                $("#files").html(data["files"]);
                $.jGrowl(data["message"]);
            }
        });
        return false;
    });

    // Select all
    $(".select-all").livequery("click", function() {
        var checked = this.checked;
        var selector = ".select-" + $(this).attr("value")
        $(selector).each(function() {
            this.checked = checked;
        });
    });

    $(".select-all-1").livequery("click", function() {
        var checked = this.checked;
        $(".select-1").each(function() {
            this.checked = checked;
        });
    });

    $(".select-all-2").livequery("click", function() {
        var checked = this.checked;
        $(".select-2").each(function() {
            this.checked = checked;
        });
    });

    // Portlets
    var overlay = $("#overlay").overlay({ closeOnClick: false, api:true, speed:100, expose: {color: '#222', loadSpeed:100 } });
    $(".portlet-edit-button").livequery("click", function() {
        tinyMCE.execCommand('mceRemoveControl', false, 'id_portlet-text');
        var url = $(this).attr("href");
        $.get(url, function(data) {
            $("#overlay .content").html(data);
            overlay.load();
            tinyMCE.execCommand('mceAddControl', true, 'id_portlet-text');
        });
        return false;
    });

    $(".portlet-add-button").livequery("click", function() {
        tinyMCE.execCommand('mceRemoveControl', false, 'id_portlet-text');
        $(this).parents("form:first").ajaxSubmit({
            success : function(data) {
                $("#overlay .content").html(data);
                overlay.load();
                tinyMCE.execCommand('mceAddControl', true, 'id_portlet-text');
        }});
        return false;
    });

    $(".ajax-portlet-save-button").livequery("click", function() {
        tinyMCE.execCommand('mceRemoveControl', false, 'id_portlet-text');
        $(this).parents("form:first").ajaxSubmit({
            success : function(data) {
                data = JSON.parse(data);
                overlay.close();
                $("#portlets").html(data["html"])
                $.jGrowl(data["message"]);
            }
        })
        return false;
    });

    $(".overlay-link").livequery("click", function() {
        var url = $(this).attr("href");
        $.get(url, function(data) {
            $("#overlay .content").html(data);
            overlay.load();
        });
        return false;
    });

    $(".overlay-close").livequery("click", function() {
        overlay.close()
    });

    // Delete dialog
    var delete_dialog = $("#yesno").overlay({ closeOnClick: false, api:true, loadSpeed: 200, top: '25%', expose: {color: '#222', loadSpeed:100 } });
    $(".delete-link").livequery("click", function() {
        $("#delete-url").html($(this).attr("href"));
        delete_dialog.load();
        return false;
    });

    var buttons = $("#yesno button").click(function(e) {
        delete_dialog.close();
        var yes = buttons.index(this) === 0;
        var url = $("#delete-url").html();
        if (yes) {
            window.location.href = url;
        }


    });

});