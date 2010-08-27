$(function() {

    // Image plugin
    $.cleditor.buttons.myimage = {
        name: "myimage",
        image: "table.gif",
        title: "Insert Image",
        useCSS: true,
        buttonClick: helloClick,
    };
    
    $.cleditor.defaultOptions.width = 670;
    $.cleditor.defaultOptions.height = 400;
    $.cleditor.defaultOptions.controls = "bold italic underline strikethrough subscript superscript " +
                                         "style | color highlight removeformat | bullets numbering | outdent " +
                                         "indent | alignleft center alignright justify | undo redo | " +
                                         "myimage link unlink | html"
    
    $.cleditor.defaultOptions.docCSSFile = "/media/tiny.css";
    $.cleditor.defaultOptions.styles = [["Paragraph", "<p>"], ["Header 1", "<h1>"], ["Header 2", "<h2>"], ["Header 3", "<h3>"]]

    var overlay = $("#overlay").overlay({
            closeOnClick: false,
            api:true,
            speed:1,
            expose: {color: '#222', loadSpeed:1 }
    });

    var editor;
    
    // Handle the hello button click event
    function helloClick(e, data) {
        editor = data.editor;
        editor.focus();        
        $.get("/manage/filebrowser?obj_id=1&type=image", function(data) {
            $("#overlay .content").html(data);
        });        
        overlay.load();
    }
    
    $("input.image").live("click", function(e) {
        var html = "<img src='" + $(this).attr("value") + "' />"
        $("#image-preview").html(html)
    })

    $("#insert-image").live("click", function(e) {            
        var url = $("input.image:checked").attr("value");
        var size = $("#image-size").val();
        var klass = $("#image-class").val();
    
        if (size)
            url = url.replace("200x200", size);
        else
            url = url.replace(".200x200", "");
        
        if (klass)
            html = "<img class='" + klass + "' src='" + url + "' />"
        else
            html = "<img src='" + url + "' />"
            
        editor.focus();
        editor.execCommand("inserthtml", html, null, null);
        overlay.close();
        return false;
    })
    
    load();
    
    // central methods to show/hide ajax loading message
    function show_ajax_loading() {
        $(".ajax-loading").show();
    };

    function hide_ajax_loading() {
        $(".ajax-loading").hide();
    };   

    function create_menu() {
        $('ul.sf-menu').superfish({
            speed: "fast",
            delay: "200"
        });
    };

    function load_object(url, tabs) {
        show_ajax_loading();
        $.get(url, function(data) {
            data = JSON.parse(data);
            for (var html in data["html"])
                $(data["html"][html][0]).html(data["html"][html][1]);
            create_menu();

            if (tabs)
                $('#manage-tabs').tabs();

            if (data["message"])
                $.jGrowl(data["message"]);
                $.cookie("message", null, { path: '/' });
            hide_ajax_loading();
        })
    };

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
        
    $(".object-add").live("click", function() {
        var url = $(this).attr("href");
        $.get(url, function(data) {
            $("#overlay .content").html(data);
            overlay.load();
        })
        return false;
    });
    
    $(".close-button").live("click", function() {
        overlay.close();
        return false;
    });

    $(".image-button").live("click", function() {
        $(this).parents("form:first").ajaxSubmit({
            success : function(data) {
                $("#hurz").html(data);
            }
        })
        return false;
    });
    
    $(".object-save-button").live("click", function() {
        var action = $(this).attr("name");
        $(this).parents("form:first").ajaxSubmit({
            data : { "action" : action },
            success : function(data) {
                data = JSON.parse(data);
                for (var html in data["html"])
                    $(data["html"][html][0]).html(data["html"][html][1]);

                // $('#manage-tabs').tabs();

                create_menu()
                
                if (data["message"])
                    $.jGrowl(data["message"]);
                
                if (data["id"]) {
                    $.bbq.pushState({ "type" : "object", "id" : data["id"] });
                    overlay.close();
                };
            }
        })
        return false;
    });

    // Load objects
    $(".manage-portal").live("click", function() {
        $.bbq.pushState({ "type" : "portal", "id" : 1 });
        return false
    });

    $(".manage-page").live("click", function() {
        var id = $(this).attr("id");
        $.bbq.pushState({ "type" : "object", "id" : id });
        return false
    });

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
    $("#manage-tabs").tabs();

    // Generic ajax save button
    $(".ajax-save-button").live("click", function() {
        show_ajax_loading();
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
                hide_ajax_loading();
            }
        })
        return false;
    });

    // Generic ajax link
    $(".ajax-link").live("click", function() {
        show_ajax_loading();        
        var url = $(this).attr("href");

        $.get(url, function(data) {
            data = JSON.parse(data);
            for (var html in data["html"])
                $(data["html"][html][0]).html(data["html"][html][1]);

            if (data["message"]) {
                $.jGrowl(data["message"]);
            }

            create_menu();
            hide_ajax_loading();
        });

        return false;
    });

    $(".reset-link").live("click", function() {
        $("input[name=name_filter]").val("");
        $("select[name=active_filter]").val("");
        return false;
    });

    $(".user-name-filter").live("keyup", function() {
        var url = $(this).attr("data");
        var value = $(this).attr("value");
        $.get(url, { "user_name_filter" : value }, function(data) {
            data = JSON.parse(data);
            for (var html in data["html"])
                $(data["html"][html][0]).html(data["html"][html][1]);
        });
    });

    // Page / Images
    $(".upload-file").live("change", function() {
        var name = $(this).attr("name");
        var number = parseInt(name.split("_")[1])
        number += 1;
        $(this).parent().after("<div><input type='file' class='upload-file' name='file_" + number + "' /></div>");
    });

    $("#page-images-save-button").live("click", function() {
        $("#page-images-form").ajaxSubmit({
            target : "#images"
        });
        return false;
    });

    $(".object-images-update-button").live("click", function() {
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

    $("#object-files-save-button").live("click", function() {
        $("#object-files-form").ajaxSubmit({
            target : "#files"
        });
        return false;
    });

    $(".object-files-update-button").live("click", function() {
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
    $(".select-all").live("click", function() {
        var checked = this.checked;
        var selector = ".select-" + $(this).attr("value")
        $(selector).each(function() {
            this.checked = checked;
        });
    });

    $(".select-all-1").live("click", function() {
        var checked = this.checked;
        $(".select-1").each(function() {
            this.checked = checked;
        });
    });

    $(".select-all-2").live("click", function() {
        var checked = this.checked;
        $(".select-2").each(function() {
            this.checked = checked;
        });
    });

    // Portlets
    $(".portlet-edit-button").live("click", function() {
        var url = $(this).attr("href");
        $.get(url, function(data) {
            $("#overlay .content").html(data);
            overlay.load();
        });
        return false;
    });

    $(".portlet-add-button").live("click", function() {
        $(this).parents("form:first").ajaxSubmit({
            success : function(data) {
                $("#overlay .content").html(data);
                overlay.load();
        }});
        return false;
    });

    $(".ajax-portlet-save-button").live("click", function() {
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

    $(".overlay-link").live("click", function() {
        var url = $(this).attr("href");
        $.get(url, function(data) {
            $("#overlay .content").html(data);
            overlay.load();
        });
        return false;
    });

    $(".overlay-close").live("click", function() {
        overlay.close()
    });

    // Delete dialog
    var delete_dialog = $("#yesno").overlay({ closeOnClick: false, api:true, loadSpeed: 200, top: '25%', expose: {color: '#222', loadSpeed:100 } });
    $(".delete-link").live("click", function() {
        $("#delete-url").html($(this).attr("href"));
        delete_dialog.load();
        return false;
    });

    var buttons = $("#yesno button").live("click", function(e) {
        delete_dialog.close();
        var yes = buttons.index(this) === 0;
        var url = $("#delete-url").html();
        if (yes) {
            load_object(url, true);
        }
    });
});