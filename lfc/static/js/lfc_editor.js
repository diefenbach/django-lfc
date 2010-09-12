$(function() {
    var editor;

    $.cleditor.defaultOptions.width = 670;
    $.cleditor.defaultOptions.height = 400;
    $.cleditor.defaultOptions.controls = "bold italic underline strikethrough subscript superscript " +
                                         "style | color highlight removeformat | bullets numbering | outdent " +
                                         "indent | alignleft center alignright justify | undo redo | " +
                                         "myimage myfile unlink | html"

    $.cleditor.defaultOptions.docCSSFile = "/media/tiny.css";
    $.cleditor.defaultOptions.styles = [["Paragraph", "<p>"], ["Header 1", "<h1>"], ["Header 2", "<h2>"], ["Header 3", "<h3>"], ["Quote", "<blockquote>"]]

    // Image plugin
    $.cleditor.buttons.myimage = {
        name: "myimage",
        image: "image.gif",
        title: "Insert Image",
        useCSS: true,
        buttonClick: imagebrowser,
    };

    // File plugin
    $.cleditor.buttons.myfile = {
        name: "myfile",
        image: "link.gif",
        title: "Insert File",
        useCSS: true,
        buttonClick: filebrowser,
    };

    // Handle the image button click event
    function imagebrowser(e, data) {
        editor = data.editor;
        editor.focus();
        var id = $("#obj-id").attr("data");
        $.get("/manage/imagebrowser?obj_id=" + id, function(data) {
            $("#overlay-2 .content").html(data);
        });
        overlay_2.load();
    }

    $("input.image").live("click", function(e) {
        var html = "<img src='" + $(this).attr("value") + "' />"
        $("#image-preview").html(html)
    })

    // File browser
    function filebrowser(e, data) {
        editor = data.editor;
        editor.focus();
        var id = $("#obj-id").attr("data");
        $.get("/manage/filebrowser?obj_id=" + id, function(data) {
            $("#overlay-2 .content").html(data);
        });
        overlay_2.load();
    }

    $("a.content-form-link").live("click", function() {
        $(".content-form").show();
        $(".extern-form").hide();
        $(".email-form").hide();
        return false;
    });

    $("a.email-form-link").live("click", function() {
        $(".content-form").hide();
        $(".extern-form").hide();
        $(".email-form").show();
        return false;
    });

    $("a.extern-form-link").live("click", function() {
        $(".content-form").hide();
        $(".extern-form").show();
        $(".email-form").hide();
        return false;
    });

    $("#insert-file").live("click", function(e) {
        var html;

        if (!html) {
            var url = $("input.child:checked").attr("value");
            if (url)
                html = "<a href='" + url + "'>" + editor.selectedText() + "</a>"
        }

        if (!html) {
            var url = $("input.fb-extern").val();
            if (url) {
                var protocol = $(".fb-extern-protocol").val();
                html = "<a href='" + protocol + url + "'>" + editor.selectedText() + "</a>"
            }
        }

        if (!html) {
            var email = $("input.fb-email").val();
            if (email != "")
                html = "<a href='mailto:" + email + "'>" + editor.selectedText() + "</a>"
        }

        if (html) {
            editor.focus();
            editor.execCommand("inserthtml", html, null, null);
        }

        overlay_2.close();
        return false;
    });

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
        overlay_2.close();
        return false;
    })

    $("a.fb-obj").live("click", function() {
        var url = $(this).attr("href");
        var id = $("#obj-id").attr("data");
        $.get(url + "&current_id=" + id, function(data) {
            $("#overlay-2 .content").html(data);
        });
        return false;
    });

    $(".image-button").live("click", function() {
        $(this).parents("form:first").ajaxSubmit({
            success : function(data) {
                $("#overlay .content").html(data);
            }
        })
        return false;
    });

});