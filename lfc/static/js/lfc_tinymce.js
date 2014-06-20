var editor;

function addEditor(selector, hide_save) {
    if (hide_save == true) {
        buttons = "bold,italic,underline,strikethrough,|,justifyleft,justifycenter,justifyright,justifyfull,|,bullist,numlist,|,forecolor,backcolor,styleselect,formatselect,image,|,link,mylink,unlink,|,removeformat,code,|,fullscreen"
    }
    else {
        buttons  = "save,bold,italic,underline,strikethrough,|,justifyleft,justifycenter,justifyright,justifyfull,|,bullist,numlist,|,forecolor,backcolor,styleselect,formatselect,image,|,link,mylink,unlink,|,removeformat,code,|,fullscreen"
    }

    // Theme options
    $(selector).tinymce({
        // Location of TinyMCE script
        script_url : '/static/tiny_mce/tiny_mce.js',

        // General options
        theme : "advanced",
        plugins : "safari,save,iespell,directionality,fullscreen,xhtmlxtras",

        theme_advanced_buttons1 : buttons,
        theme_advanced_buttons2 : "",
        theme_advanced_buttons3 : "",
        theme_advanced_buttons4 : "",
        theme_advanced_toolbar_location : "top",
        theme_advanced_toolbar_align : "left",
        save_onsavecallback : "save",
        relative_urls : false,
        height : "480",
        cleanup : false,
        content_css : "/static/css/tiny.css",
        // theme_advanced_statusbar_location : "bottom",
        // theme_advanced_resizing : true,

        setup : function(ed) {
            ed.addButton('link', {
                onclick : function(e) {
                    filebrowser(e, ed);
                }
            });

            ed.addButton('image', {
                onclick : function(e) {
                    imagebrowser(e, ed);
                }
            });

        }
   });
};

function insertHTML(html) {
    editor.selection.setContent(html);
}

function getSelectedNode() {
    return editor.selection.getNode();
}

function getSelectedText() {
    content = editor.selection.getContent();
    if (content.indexOf("<img") != -1) {
        return content;
    }
    else {
        return editor.selection.getContent({format : 'text'});
    }
}

function update_editor() {
    /* for each field first detach tinymce and then attach again */
    $(".wysiwyginput").each(function(idx) {
        if (typeof(tinyMCE) != 'undefined') {
            var obj = $(this);
            if (obj.length > 0){
                obj.tinymce().remove();
            }
        }
        addEditor(obj, false);
    });
}

function save(ed) {
    $("#" + ed.id).parents("form:first").ajaxSubmit({
        dataType: "json",
        success : function(data) {
            show_message(data["message"]);
        }
    })
}

function filebrowser(e, ed) {
    editor = ed;
    node = editor.selection.getNode();
    url = node.href || "";
    title = node.title || "";
    target = node.target || "";

    var id = $("#obj-id").attr("data");
    $.get("/manage/filebrowser?obj_id=" + id + "&url=" + url + "&title=" + title + "&target=" + target, function(data) {
        data = $.parseJSON(data);
        $("#overlay-2 .content").html(data["html"]);
        switch (data["current_view"]) {
            case "mail": display_mail(); break;
            case "content": display_content(); break;
            case "extern": display_extern(); break;
        }
    });
    overlay_2.load();
    $("#overlay-2").css("left", ($(document).width() - 1000) / 2);
}

function imagebrowser(e, ed) {
    editor = ed;
    node = editor.selection.getNode();
    url = node.src || "";
    title = node.title || "";
    klass = node.className || ""
    var id = $("#obj-id").attr("data");
    $.get("/manage/imagebrowser?obj_id=" + id + "&url=" + url + "&title=" + title + "&class=" + klass, function(data) {
        data = $.parseJSON(data);
        $("#overlay-2 .content").html(data["html"]);
    });
    overlay_2.load();
    $("#overlay-2").css("left", ($(document).width() - 1000) / 2);
}
