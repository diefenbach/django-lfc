$(function() {

    load();

    var overlay = $("#overlay").overlay({
            closeOnClick: false,
            api:true,
            speed:1,
            expose: {color: '#222', loadSpeed:1 }
    });

    $(".object-add").livequery("click", function() {
        var url = $(this).attr("href");
        $.get(url, function(data) {
            $("#overlay .content").html(data);
            overlay.load();
        })
        return false;
    });
    
    $(".close-button").livequery("click", function() {
        overlay.close();
        return false;
    });
    
    $(".object-save-button").livequery("click", function() {
        var action = $(this).attr("name");
        $(this).parents("form:first").ajaxSubmit({
            data : { "action" : action },
            success : function(data) {
                data = JSON.parse(data);
                for (var html in data["html"])
                    $(data["html"][html][0]).html(data["html"][html][1]);

                $('#manage-tabs > ul').tabs({ cookie: { expires: 30 } });

                create_menu()
                
                if (data["message"])
                    $.jGrowl(data["message"]);
                
                if (data["id"]) {
                    $.bbq.pushState({ "object" : data["id"] });
                    overlay.close();
                };
            }
        })
        return false;
    });

    function create_menu() {
        $('ul.sf-menu').superfish({
            speed: "fast",
            delay: "200"
        });
    };

    function load_object(url, tabs) {
        $.get(url, function(data) {
            data = JSON.parse(data);
            for (var html in data["html"])
                $(data["html"][html][0]).html(data["html"][html][1]);
            create_menu();

            if (tabs)
                $('#manage-tabs > ul').tabs({ cookie: { expires: 30 } });

            if (data["message"])
                $.jGrowl(data["message"]);
                $.cookie("message", null, { path: '/' });
        })
    };

    // Load objects
    $(".manage-portal").livequery("click", function() {
        $.bbq.pushState({ "type" : "portal", "id" : 1 });
        return false
    });

    $(".manage-page").livequery("click", function() {
        var id = $(this).attr("id");
        $.bbq.pushState({ "type" : "object", "id" : id });
        return false
    });

    function load() {
        type = $.bbq.getState('type');
        id = $.bbq.getState('id');
        
        if (type == "portal") {
            load_object("/manage/load-portal", true);
        }
        else {
            if ($("#portal").length | !$("#core_data").length) {
                load_object("/manage/load-object/" + id, true);
            }
            else {
                load_object("/manage/load-object-parts/" + id, false);
            }
        }
    }

    $(window).bind('hashchange', function( event ) {
        load()
    });

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

    // Tabs
    $('#manage-tabs > ul').tabs({ cookie: { expires: 30 } });

    // Generic ajax save button
    $(".ajax-save-button").livequery("click", function() {
        $(".ajax-loading").show()
        var action = $(this).attr("name");
        $(this).parents("form:first").ajaxSubmit({
            data : {"action" : action },
            success : function(data) {
                data = JSON.parse(data);
                for (var html in data["html"])
                    $(data["html"][html][0]).html(data["html"][html][1]);
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

            create_menu();
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
    $(".portlet-edit-button").livequery("click", function() {
        var url = $(this).attr("href");
        $.get(url, function(data) {
            $("#overlay .content").html(data);
            overlay.load();
        });
        return false;
    });

    $(".portlet-add-button").livequery("click", function() {
        $(this).parents("form:first").ajaxSubmit({
            success : function(data) {
                $("#overlay .content").html(data);
                overlay.load();
        }});
        return false;
    });

    $(".ajax-portlet-save-button").livequery("click", function() {
        $(this).parents("form:first").ajaxSubmit({
            success : function(data) {
                data = JSON.parse(data);
                if (data["success"]) {
                    overlay.close();
                    $("#portlets").html(data["html"])
                }
                else {
                    $("#overlay .content").html(data["html"]);
                }
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

    var buttons = $("#yesno button").livequery("click", function(e) {
        delete_dialog.close();
        var yes = buttons.index(this) === 0;
        var url = $("#delete-url").html();
        if (yes) {
            load_object(url, true);
        }
    });

});